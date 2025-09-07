"""
한성대학교 공지사항 크롤링 설정 파일
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# 기본 설정
RSS_URL = 'https://www.hansung.ac.kr/bbs/hansung/143/rssList.do?page={}'
BASE_DOMAIN = "https://www.hansung.ac.kr"
DB_FILENAME = "notice_db.txt"
OUTPUT_DIR = "./pdf"

# OpenAI 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "gpt-4o-mini"

# 세부적인 카테고리를 대표 카테고리로 통일하기 위한 map
CATEGORY_MAP = {
    # 취업
    "강소기업채용": "취업",
    "채용정보": "취업",
    "인턴쉽": "취업",
    "교육프로그램": "취업",
    "고시반": "취업",
    "기타": "취업",

    # 장학
    "국가장학금": "장학",
    "교외장학금": "장학",
    "교내장학금": "장학",
    "면학근로": "장학",
    "학자금대출": "장학",
    "국가근로": "장학",
    "공모전 등": "장학",
    "비교과장학": "장학",

    # 창업
    "창업정보": "창업",
    "창업공모전": "창업",
    "창업행사": "창업",
    "기타": "창업",
}

# 크롤링 설정
DEFAULT_MAX_PAGES = 1
REQUEST_TIMEOUT = 30  # HTTP 요청 타임아웃 (초)
OCR_DELAY = 2  # OCR 처리 전 대기 시간 (초)