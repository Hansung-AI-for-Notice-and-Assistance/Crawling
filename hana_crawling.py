"""
HANA (Hansung AI for Notice & Assistance)
한성대학교 공지사항 크롤링 모듈

이 파일은 한성대학교 공지사항을 크롤링하고 AI를 활용하여 신청기간을 추출하는 기능을 제공합니다.
- RSS 피드 크롤링
- HTML 페이지 크롤링
- OCR 이미지 텍스트 추출
"""

import re
import asyncio
import requests
from bs4 import BeautifulSoup as bs
from markdownify import markdownify as md

from hana_crawler_config import RSS_URL, BASE_DOMAIN, DEFAULT_MAX_PAGES, MIN_TEXT_LENGTH, AI_CALL_DELAY
from hana_utils import (
    normalize_category, get_application_period, image_urls_to_text,
    is_stop, load_latest_crawled_id, save_latest_crawled_id
)


# HTML 크롤링 함수
def html_crawl(link, base_domain=BASE_DOMAIN):
    """
    공지사항 게시글을 조회하여 내용, 사진, 첨부파일을 수집합니다.
    
    Args:
        link (str): 공지사항 URL
        base_domain (str): 기본 도메인
        
    Returns:
        tuple[str | None, list[str], list[str]]: (본문, 이미지 URL 목록, 첨부파일 목록)
    """

    page = requests.get(link)
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
async def rss_crawl(db, max_pages=DEFAULT_MAX_PAGES, initial=False, rss_url=RSS_URL, base_domain=BASE_DOMAIN):
    """
    RSS 피드를 순회하여 제목, 링크, 게시일, 카테고리를 수집하고 크롤링합니다.
    
    Args:
        db: 데이터베이스 객체
        max_pages (int): 최대 크롤링 페이지 수
        initial (bool): 초기 크롤링 여부 (True=초기, False=일일)
        rss_url (str): RSS URL 템플릿
        base_domain (str): 기본 도메인
    """

    saved_cnt = 0
    ocr_count = 0
    
    # 마지막 크롤링 ID 로드
    latest_crawled_id = load_latest_crawled_id()
    
    # 가장 최신 ID 저장용
    newest_id = None

    for page_number in range(1, max_pages+1):
        url = rss_url.format(page_number)
        page = requests.get(url)
            
        soup = bs(page.text, 'xml')
        items = soup.find_all('item')

        if not items:
            break

        for item in items:
            title = item.find('title').get_text(strip=True) if item.find('title') else ""
            link = item.find('link').get_text(strip=True) if item.find('link') else ""
            pub_date = item.find('pubDate').get_text(strip=True) if item.find('pubDate') else ""
            category = item.find('category').get_text(strip=True) if item.find('category') else ""

            # 공지사항 ID 추출
            match = re.search(r'143/(\d+)', link)
            notice_id = match.group(1) if match else "unknown"

            # 초기 크롤링인 경우 날짜 체크 - 작년 어제 이전 공지면 중단
            if initial and is_stop(pub_date):
                return

            # 중복 체크 - 마지막 크롤링 ID와 같으면 중단
            if latest_crawled_id and notice_id == latest_crawled_id:
                return
            
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
                
                ocr_content = await image_urls_to_text(image_urls)
                if ocr_content and len(ocr_content) > len(content):
                    content = ocr_content
            
            # 최종 신청기간
            start_date, end_date = None, None
            if content:
                # 레이트리밋 방지를 위한 지연
                await asyncio.sleep(AI_CALL_DELAY)
                start_date, end_date = get_application_period(content)
                if end_date and not start_date:
                    # pub_date에서 시간 제거
                    clean_pub_date = pub_date.split(' ')[0] if ' ' in pub_date else pub_date
                    start_date = clean_pub_date
                
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
            
            # 가장 최신 ID 저장 (첫 번째 크롤링한 것이 가장 최신)
            if newest_id is None:
                newest_id = notice_id
            
    print(f"총 {saved_cnt}개의 공지사항이 성공적으로 저장되었습니다!")
    print(f"OCR을 실행한 공지는 총 {ocr_count}개입니다.")
    
    # 가장 최신 ID 저장
    if newest_id:
        save_latest_crawled_id(newest_id)
        print(f"가장 최신 ID 저장: {newest_id}")
