"""
HANA (Hansung AI for Notice & Assistance)
한성대학교 공지사항 크롤링 모듈

이 파일은 한성대학교 공지사항을 크롤링하고 AI를 활용하여 신청기간을 추출하는 기능을 제공합니다.
- RSS 피드 크롤링
- HTML 페이지 크롤링
- OCR 이미지 텍스트 추출
"""

import re
import requests
import json
from datetime import datetime
from bs4 import BeautifulSoup as bs
from markdownify import markdownify as md
from openai import OpenAI

from hana_crawler_config import RSS_URL, BASE_DOMAIN, DEFAULT_MAX_PAGES, REQUEST_TIMEOUT, MIN_TEXT_LENGTH
from hana_utils import normalize_category, get_application_period, image_urls_to_text


# HTML 크롤링 함수
def html_crawl(url, base_domain=BASE_DOMAIN):
    """
    공지사항 게시글을 조회하여 내용, 사진, 첨부파일을 수집합니다.
    
    Args:
        url (str): 공지사항 URL
        base_domain (str): 기본 도메인
        
    Returns:
        tuple: (content, image_urls, attachments)
    """
    try:
        page = requests.get(url, timeout=REQUEST_TIMEOUT)
        page.raise_for_status()
    except requests.RequestException as e:
        print(f"HTML 크롤링 요청 실패: {url} - {e}")
        return None, [], []
    
    soup = bs(page.text, 'html.parser')

    # 본문 내용, 사진 링크들, 첨부파일들
    content, image_urls, attachments = None, [], []

    # 내용 및 사진
    view_con_div = soup.find('div', class_='view-con')
    if view_con_div:
        content = md(str(view_con_div), strip=['a', 'img']).strip()
        
        # 이미지 URL 추출
        for img_tag in view_con_div.find_all('img', src=True):
            src = img_tag['src']
            if src.startswith('/'):
                src = f"{base_domain}{src}"
            image_urls.append(src)

    # 첨부파일
    file_div = soup.find('div', class_='view-file')
    if file_div:
        for a_tag in file_div.find_all('a', href=True):
            href = a_tag['href']
            # 다운로드 링크만 필터링
            if "download.do" in href:
                if href.startswith('/'):
                    file_url = f"{base_domain}{href}"
                file_name = a_tag.get_text(strip=True)
                attachments.append(f"{file_name} | {file_url}")
    
    return content, image_urls, attachments


# RSS 크롤링 메인 함수
async def rss_crawl(db, max_pages=DEFAULT_MAX_PAGES, rss_url=RSS_URL, base_domain=BASE_DOMAIN):
    """
    RSS 피드를 순회하여 제목, 링크, 게시일, 카테고리를 수집하고 크롤링합니다.
    
    Args:
        db: 데이터베이스 객체
        max_pages (int): 최대 크롤링 페이지 수
        rss_url (str): RSS URL 템플릿
        base_domain (str): 기본 도메인
        
    Returns:
        None
    """
    saved_cnt = 0
    ocr_count = 0

    for page_number in range(1, max_pages+1):
        url = rss_url.format(page_number)
        try:
            page = requests.get(url, timeout=REQUEST_TIMEOUT)
            page.raise_for_status()
        except requests.RequestException as e:
            print(f"RSS 요청 실패: {url} - {e}")
            continue
            
        soup = bs(page.text, 'xml')
        items = soup.find_all('item')

        if not items:
            print(f"{page_number} 페이지에 더 이상 게시물이 없습니다.")
            break

        for item in items:
            title = item.find('title').get_text(strip=True) if item.find('title') else "No Title"
            link = item.find('link').get_text() if item.find('link') else "No Link"
            pub_date = item.find('pubDate').get_text(strip=True) if item.find('pubDate') else "No Date"
            category = item.find('category').get_text(strip=True) if item.find('category') else "No Category"

            # 카테고리 정규화
            category = normalize_category(category)

            # 절대 경로로 변경
            if link.startswith("/"):
                link = f"{base_domain}{link}"

            # HTML 크롤링 (내용, 이미지, 첨부파일)
            content, image_urls, attachments = html_crawl(link)
            
            # OCR 처리
            if not content and image_urls:
                # 텍스트가 없고 이미지만 있는 경우
                ocr_count += 1
                
                content = await image_urls_to_text(image_urls)
            elif content and len(content) < MIN_TEXT_LENGTH and image_urls:
                # 텍스트가 짧고 이미지가 있는 경우 OCR도 시도
                ocr_count += 1
                
                print(f"-> 텍스트가 짧아서 OCR도 시도: {title} (텍스트 길이: {len(content)}자)")
                ocr_content = await image_urls_to_text(image_urls)
                if ocr_content and len(ocr_content) > len(content):
                    content = ocr_content
            
            # 최종 신청기간 추출
            start_date, end_date = None, None
            if content:
                start_date, end_date = get_application_period(content)
                if end_date and not start_date:
                    start_date = pub_date
                
            # 공지사항 ID 추출
            match = re.search(r'143/(\d+)', link)
            notice_id = match.group(1) if match else "unknown"

            # DB에 저장
            db.save_notice(
                notice_id=notice_id,
                title=title,
                link=link,
                pub_date=pub_date,
                category=category,
                start_date=start_date,
                end_date=end_date,
                content=content,
                image_urls=image_urls,
                attachments=attachments
            )
            saved_cnt += 1
            
    print(f"총 {saved_cnt}개의 공지사항이 성공적으로 저장되었습니다!")
    print(f"OCR을 실행한 공지는 총 {ocr_count}개입니다.")
