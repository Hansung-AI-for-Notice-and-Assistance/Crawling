import os

class FileDB: # .txt 파일로 저장
    def __init__(self, filename="notice_db.txt", format="txt"):
        self.filename = filename
        self.format = format
        self.saved_notices = set()  # 중복 방지용

        # 파일 없으면 새로 생성
        if not os.path.exists(self.filename):
            with open(self.filename, "w", encoding="utf-8") as f:
                f.write("===== Notice DB Start =====\n\n")

    def save_notice(self, notice_id, title, link, date, category, content, image_urls=None, attachments=None):
        """공지사항을 .txt 파일에 저장"""
        # 중복 체크
        if notice_id in self.saved_notices:
            print(f"이미 저장된 공지사항 건너뜀: {notice_id}")
            return False

        image_urls = image_urls or []
        attachments = attachments or []

        try:
            with open(self.filename, "a", encoding="utf-8") as f:
                f.write(f"ID: {notice_id}\n")
                f.write(f"제목: {title}\n")
                f.write(f"링크: {link}\n")
                f.write(f"게시 날짜: {date}\n")
                f.write(f"카테고리: {category}\n")
                
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
            
            self.saved_notices.add(notice_id)
    
            return True
            
        except Exception as e:
            print(f"공지사항 저장 실패: {title} - {e}")
            return False