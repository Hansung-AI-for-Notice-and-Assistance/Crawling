import os
import requests
import img2pdf
import asyncio
import unicodedata
from dotenv import load_dotenv
from pyzerox import zerox

from config import MODEL, OUTPUT_DIR, REQUEST_TIMEOUT, OCR_DELAY

# 프로그램 시작 시 출력 디렉토리가 없으면 생성
os.makedirs(OUTPUT_DIR, exist_ok=True)


# 함수 정의
def clean_text(text):
    """텍스트에서 문제가 될 수 있는 특수 문자들을 정리"""
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

# 이미지 URL들을 PDF로 변환
def images_to_pdf(image_urls, pdf_path):
    try:
        image_data_list = []
        
        # 모든 이미지를 다운로드
        for url in image_urls:
            try:
                response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
                response.raise_for_status()
                image_data_list.append(response.content)
            except requests.RequestException as e:
                print(f"이미지 다운로드 실패: {url} - {e}")
                continue
        
        # img2pdf를 사용하여 PDF 생성
        if image_data_list:
            pdf_bytes = img2pdf.convert(image_data_list)
            with open(pdf_path, "wb") as f:
                f.write(pdf_bytes)
            return True
        else:
            print("다운로드된 이미지가 없습니다")
            return False
            
    except Exception as e:
        print(f"이미지-PDF 변환 중 오류 발생: {e}")
        return False

# PDF에서 텍스트 추출
async def pdf_zerox(file_path):
    try:
        result = await zerox(
            file_path=file_path,
            model=MODEL,
            output_dir=None
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

# 이미지 URL에서 텍스트 추출
async def image_urls_to_text(image_urls):
    temp_pdf_path = os.path.join(OUTPUT_DIR, "temp.pdf")
        
    try:
        # 이미지를 PDF로 변환
        if not images_to_pdf(image_urls, temp_pdf_path):
            print("PDF 변환 실패")
            return ""
            
        # API 호출 전 딜레이
        await asyncio.sleep(OCR_DELAY)
            
        # OCR 처리
        content = await pdf_zerox(temp_pdf_path)
        if content:
            #print("OCR 텍스트 추출 성공")
            return content
        else:
            print("OCR 텍스트 추출 실패")
            return ""
                
    finally:
        # 임시 파일 정리
        try:
            if os.path.exists(temp_pdf_path):
                os.remove(temp_pdf_path)
                #print(f"임시 파일 삭제: {temp_pdf_path}")
        except OSError as e:
            print(f"임시 파일 삭제 실패: {e}")