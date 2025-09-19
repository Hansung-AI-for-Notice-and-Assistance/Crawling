"""
HANA 크롤링 시스템 실행 파일

이 파일은 크롤링 시스템의 메인 실행 로직을 담당합니다.
- 초기 크롤링 vs 일일 크롤링 구분
- 데이터베이스 관리
- Node 서버 전송
"""

import asyncio
import sys
import time
from db import FileDB
from hana_crawling import rss_crawl
from hana_utils import (
    is_initial_crawl, remove_notice_db, reset_database, send_to_file
)


def main():
    """메인 실행 함수"""
    # 명령행 인수 확인
    if len(sys.argv) > 1 and sys.argv[1] == "reset":
        reset_database()
        return

    initial = is_initial_crawl()
    print("초기 크롤링" if initial else "일일 크롤링")

    max_pages = 1 if initial else 2 # 초기 적재 테스트용 1

    # 일일 크롤링인 경우 notice_db.txt 삭제
    if not initial:
        remove_notice_db()

    # DB 정의
    file_db = FileDB()

    # 크롤링 시간 측정
    start_ts = time.perf_counter()

    # 크롤링 실행
    print("HANA 크롤링 시스템 시작...\n")
    asyncio.run(rss_crawl(
        db=file_db,
        max_pages=max_pages,
        initial=initial
    ))
    print("크롤링 완료!\n")

    elapsed = time.perf_counter() - start_ts
    hours = int(elapsed // 3600)
    minutes = int((elapsed % 3600) // 60)
    seconds = int(elapsed % 60)
    if hours:
        print(f"소요시간: {hours}시간 {minutes}분 {seconds}초, {elapsed:.2f}초")
    else:
        print(f"소요시간: {minutes}분 {seconds}초, {elapsed:.2f}초")

    # FastAPI 서버로 결과 파일 전송
    send_to_file("notice_db.txt")
    

if __name__ == "__main__":
    main()
