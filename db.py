import os

class FileDB: # .txt 파일로 저장
    def __init__(self, filename="notice_db.txt", format="txt"):
        self.filename = filename
        self.format = format

        # 파일 없으면 새로 생성
        if not os.path.exists(self.filename):
            with open(self.filename, "w", encoding="utf-8") as f:
                pass

    def save_notice(self, notice_id, title, link, pub_date, category, 
        start_date, end_date, content, image_urls=None, attachments=None):

        image_urls = image_urls or []
        attachments = attachments or []

        with open(self.filename, "a", encoding="utf-8") as f:
            f.write(f"ID: {notice_id}\n")
            f.write(f"제목: {title}\n")
            f.write(f"링크: {link}?layout=unknown\n")
            f.write(f"게시 날짜: {pub_date}\n")
            f.write(f"카테고리: {category}\n")
            f.write(f"시작일: {start_date if start_date else '없음'}\n")
            f.write(f"종료일: {end_date if end_date else '없음'}\n")
            
            if image_urls:
                f.write("이미지 URL:\n")
                for img in image_urls:
                    f.write(f"\t- {img}\n")
            else:
                f.write("이미지 URL: 없음\n")
            
            if attachments:
                f.write("첨부파일:\n")
                for att in attachments:
                    f.write(f"\t- {att}\n")
            else:
                f.write("첨부파일: 없음\n")
            
            f.write(f"내용:\n{content}\n")
            f.write("\n" + "-" * 50 + "\n\n")