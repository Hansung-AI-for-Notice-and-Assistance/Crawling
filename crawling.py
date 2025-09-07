import re
import requests
from bs4 import BeautifulSoup as bs
from markdownify import markdownify as md

from ocr import image_urls_to_text
from config import RSS_URL, BASE_DOMAIN, CATEGORY_MAP, DEFAULT_MAX_PAGES, REQUEST_TIMEOUT


# 함수 정의

# 카테고리 정규화 함수
def normalize_category(category):
    return CATEGORY_MAP.get(category, category)

# 공지사항 게시글을 조회하여 내용, 사진, 첨부파일 수집하는 함수
def html_crawl(url, base_domain=BASE_DOMAIN):
    try:
        page = requests.get(url, timeout=REQUEST_TIMEOUT)
        page.raise_for_status()
    except requests.RequestException as e:
        print(f"HTML 크롤링 요청 실패: {url} - {e}")
        return "", [], []
    
    soup = bs(page.text, 'html.parser')

    # 본문 내용, 사진 링크들, 첨부파일들
    content, image_urls, attachments = "", [], []

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

# RSS 피드를 순회하여 제목, 링크, 게시일, 카테고리 수집하는 함수
async def rss_crawl(db, max_pages=DEFAULT_MAX_PAGES, rss_url=RSS_URL, base_domain=BASE_DOMAIN):
    saved_cnt = 0
    image_only_count = 0

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

            # 내용, 사진, 첨부파일들
            content, image_urls, attachments = html_crawl(link, base_domain)

            # 내용은 없고, 이미지 URL은 있는지 확인
            if image_urls and content == "":
                image_only_count += 1
                print(f"-> 이미지만 존재하는 공지 발견: {title}")

                # OCR로 이미지 텍스트 추출
                content = await image_urls_to_text(image_urls)

            # 공지사항 ID 추출, '143/' 뒤에 오는 숫자 그룹을 찾는 정규표현식
            match = re.search(r'143/(\d+)', link)
            notice_id = match.group(1)

            # DB에 저장
            db.save_notice(
                notice_id=notice_id,
                title=title,
                link=link,
                date=pub_date,
                category=category,
                content=content,
                image_urls=image_urls,
                attachments=attachments
            )
            saved_cnt += 1
            
    print(f"총 {saved_cnt}개의 공지사항이 성공적으로 저장되었습니다!")
    print(f"이미지만 있는 공지는 총 {image_only_count}개입니다.")