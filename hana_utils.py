"""
HANA (Hansung AI for Notice & Assistance)
유틸리티 함수 모음

이 파일은 HANA 크롤링 시스템에서 사용되는 기본적인 유틸리티 함수들을 포함합니다.
- 카테고리 매핑 처리
- AI 기반 신청기간 추출
- 이미지 URL -> 텍스트 추출
- 크롤링 상태 관리 (초기/일일 크롤링 구분)
- 데이터베이스 파일 관리
"""

import os
import json
import asyncio
import img2pdf
import requests
from datetime import datetime, timedelta
from openai import OpenAI
from pyzerox import zerox

from hana_crawler_config import (
    CATEGORY_MAP, OPENAI_API_KEY, MODEL, TEMPERATURE, MAX_TOKENS, PROMPT, PDF_PATH, OCR_DELAY
)


def normalize_category(category):
    """
    카테고리를 정규화합니다.
    
    Args:
        category (str): 원본 카테고리명
        
    Returns:
        str: 정규화된 카테고리명
    """
    return CATEGORY_MAP.get(category, category)


def get_application_period(content):
    """
    OpenAI API를 사용하여 공지사항 본문에서 신청기간을 추출합니다.
    
    Args:
        content (str): 공지사항 본문 내용
        
    Returns:
        tuple[str | None, str | None]: (시작일, 종료일)
    """
    if not content:
        return None, None
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        # 프롬프트 템플릿 사용
        prompt = PROMPT.format(
            content=content
        )

        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS
        )

        # AI 응답 파싱
        ai_response = response.choices[0].message.content.strip()
        
        # 빈 응답 체크
        if not ai_response:
            print("AI 응답이 비어있습니다.")
            return None, None
        
        try:
            result = json.loads(ai_response)
            
            if result.get('has_period', False):
                start_date = result.get('start_date')
                end_date = result.get('end_date')
                return start_date, end_date
            else:
                return None, None
                
        except json.JSONDecodeError as e:
            print(f"JSON 형식 X: {e}")
            print(f"AI 응답: {ai_response}")
            return None, None
        except Exception as e:
            print(f"파싱 오류: {e}")
            return None, None
            
    except Exception as e:
        print(f"AI 신청기간 추출 실패: {e}")
        return None, None


def images_to_pdf(image_urls):
    """
    이미지 URL들을 PDF로 변환합니다.
    
    Args:
        image_urls (list): 이미지 URL 리스트
        
    Returns:
        bool: 변환 성공 여부
    """
    try:
        # 출력 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(PDF_PATH), exist_ok=True)
        
        image_list = []
        
        # 모든 이미지를 다운로드
        for url in image_urls:
            try:
                response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
                response.raise_for_status()
                image_list.append(response.content)
            except requests.RequestException as e:
                print(f"이미지 다운로드 실패: {url} - {e}")
                continue
        
        # PDF 생성
        if image_list:
            pdf_bytes = img2pdf.convert(image_list)
            with open(PDF_PATH, "wb") as f:
                f.write(pdf_bytes)
            return True
        else:
            print("다운로드된 이미지가 없습니다")
            return False
            
    except Exception as e:
        print(f"이미지 -> PDF 변환 중 오류 발생: {e}")
        return False


async def get_text_from_pdf(file_path):
    """
    PDF에서 zerox를 사용하여 텍스트를 추출합니다.
    
    Args:
        file_path (str): PDF 파일 경로
        
    Returns:
        str | None: 추출된 텍스트
    """
    try:
        result = await zerox(
            file_path=file_path,
            model=MODEL
            )
        
        content = ""
        for page in result.pages:
            content += page.content + "\n\n"
        
        return content
    
    except Exception as e:
        print(f"OCR 처리 실패: {e}")
        return None


async def image_urls_to_text(image_urls):
    """
    이미지 URL들에서 텍스트를 추출합니다.
    
    Args:
        image_urls (list[str]): 이미지 URL 리스트
        
    Returns:
        str | None: 추출된 텍스트
    """
    try:
        # 이미지를 PDF로 변환 (임시 파일 자동 생성)
        if not images_to_pdf(image_urls):
            print("PDF 변환 실패")
            return None
            
        # API 호출 전 딜레이
        await asyncio.sleep(OCR_DELAY)
            
        # OCR 처리
        content = await get_text_from_pdf(PDF_PATH)
        if content:
            return content
        else:
            print("OCR 텍스트 추출 실패")
            return ""
                
    finally:
        # 임시 파일 정리
        try:
            if os.path.exists(PDF_PATH):
                os.remove(PDF_PATH)
        except OSError as e:
            print(f"임시 파일 삭제 실패: {e}")


def is_initial_crawl():
    """
    초기 크롤링인지 확인합니다.
    
    Returns:
        bool: 초기 크롤링 여부. notice_db.txt 파일이 없으면 True
    """
    return not os.path.exists("notice_db.txt")


def is_stop(pub_date):
    """
    크롤링을 중단해야 하는지 확인합니다.
    
    Args:
        pub_date (str): 공지사항 게시일 (예: "2025-09-16 14:30:00" 또는 "2025-09-16")
        
    Returns:
        bool: 크롤링 중단 여부
    """
    # pub_date 파싱 (시간 부분 제거)
    if ' ' in pub_date:
        pub_date = pub_date.split(' ')[0]
    
    # 작년 어제 날짜 계산
    last_year_yesterday = datetime.now() - timedelta(days=365)
    target_date = last_year_yesterday.strftime("%Y-%m-%d")
    
    if pub_date < target_date:
        return True
        
    return False


def load_latest_crawled_id():
    """
    마지막으로 크롤링한 공지 ID를 로드합니다.
    
    Returns:
        str | None: 마지막 크롤링 ID (파일이 없거나 비어있으면 None)
    """
    if os.path.exists("crawled_id.txt"):
        with open("crawled_id.txt", "r", encoding="utf-8") as f:
            latest_id = f.read().strip()
            return latest_id if latest_id else None
    return None


def save_latest_crawled_id(notice_id):
    """
    마지막으로 크롤링한 공지 ID를 저장합니다.
    
    Args:
        notice_id (str): 저장할 공지 ID
    """
    with open("crawled_id.txt", "w", encoding="utf-8") as f:
        f.write(notice_id)


def remove_notice_db():
    """
    notice_db.txt 파일만 삭제합니다 (일일 크롤링용).
    """
    if os.path.exists("notice_db.txt"):
        os.remove("notice_db.txt")


def reset_database():
    """
    데이터베이스 파일들을 삭제합니다 (초기화).
    """
    files_to_delete = ["notice_db.txt", "crawled_id.txt"]
    
    for filename in files_to_delete:
        if os.path.exists(filename):
            os.remove(filename)
