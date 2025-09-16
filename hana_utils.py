"""
HANA (Hansung AI for Notice & Assistance)
유틸리티 함수 모음

이 파일은 HANA 크롤링 시스템에서 사용되는 기본적인 유틸리티 함수들을 포함합니다.
- 카테고리 매핑 처리
- AI 기반 신청기간 추출
- 텍스트 정리 및 특수문자 처리
- 이미지 -> PDF 변환
- PDF 텍스트 추출
- 이미지 URL -> 텍스트 추출
"""

import os
import json
import asyncio
import img2pdf
import requests
import unicodedata
from datetime import datetime
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
        tuple: (start_date, end_date) 또는 (None, None)
    """
    if not content:
        return None, None
    
    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        
        current_year = datetime.now().year
        
        # 프롬프트 템플릿 사용
        prompt = PROMPT.format(
            content=content,
            current_year=current_year
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


def clean_text(text):
    """
    텍스트에서 문제가 될 수 있는 특수 문자들을 정리합니다.
    
    Args:
        text (str): 정리할 텍스트
        
    Returns:
        str: 정리된 텍스트
    """
    if not text:
        return ""
    
    # 유니코드 정규화
    text = unicodedata.normalize('NFKD', text)
    
    # 특수 문자들을 일반 문자로 변환하거나 제거
    replacements = {
        '\u2613': '☒',  # ballot box with x
        '\u2610': '☐',  # ballot box
        '\u2611': '☑',  # ballot box with check
        '\u2713': '✓',  # check mark
        '\u2717': '✗',  # ballot x
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    # 제어 문자 제거 (탭, 개행 등은 유지)
    text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C' or char in '\t\n\r')
    
    return text.strip()


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
        str: 추출된 텍스트 또는 None
    """
    try:
        result = await zerox(
            file_path=file_path,
            model=MODEL
        )
        
        # ZeroxOutput 객체인 경우 pages에서 텍스트 추출
        if hasattr(result, 'pages'):
            content = ""
            for page in result.pages:
                if hasattr(page, 'content'):
                    content += page.content + "\n\n"
            return clean_text(content)
        
        # dict인 경우
        if isinstance(result, dict):
            content = result.get("markdown", "내용을 추출하지 못했습니다.")
            return clean_text(content)
        
        # 기타 경우
        return clean_text(str(result))
    
    except Exception as e:
        print(f"OCR 처리 실패: {e}")
        return None


async def image_urls_to_text(image_urls):
    """
    이미지 URL들에서 텍스트를 추출합니다.
    
    Args:
        image_urls (list): 이미지 URL 리스트
        
    Returns:
        str: 추출된 텍스트
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
