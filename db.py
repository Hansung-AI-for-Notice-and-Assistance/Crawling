import os
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from openai import OpenAI

class FileDB: # .txt 파일로 저장
    def __init__(self, filename="notice_db.txt", format="txt"):
        self.filename = filename
        self.format = format

        # 파일 없으면 새로 생성
        if not os.path.exists(self.filename):
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write("===== Notice DB Start =====\n\n")

    def save_notice(self, notice_id, title, link, date, category, content, image_url=None, attachments=None):
        """공지사항을 .txt 파일에 저장"""
        image_url = image_url or ""
        attachments = attachments or []

        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(f"ID: {notice_id}\n")
            f.write(f"제목: {title}\n")
            f.write(f"링크: {link}\n")
            f.write(f"게시 날짜: {date}\n")
            f.write(f"카테고리: {category}\n")
            f.write(f"이미지 URL: {image_url}\n")
            f.write(f"내용: {content[:100]}...\n")  # 본문은 길면 앞 100자만 저장

            if attachments:
                f.write("첨부파일:\n")
                for idx, att in enumerate(attachments, start=1):
                    f.write(f"\t{idx}. {att}\n")
            else:
                f.write("첨부파일: 없음\n")

            f.write("\n" + "-" * 50 + "\n\n")

        # print(f"공지사항 '{title}' 저장 완료!")