import imaplib
import email
from email.header import decode_header
import os
import re
import requests
import shutil
from dotenv import load_dotenv
import blog_copy_replace_file
from urllib.parse import unquote


load_dotenv()

EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
IMAP_SERVER = os.getenv("IMAP_SERVER")
NOTION_FILE_TOKEN = os.getenv("NOTION_FILE_TOKEN")


# 创建IMAP4对象
mail = imaplib.IMAP4_SSL(IMAP_SERVER)

# 登录
mail.login(EMAIL_USERNAME, EMAIL_PASSWORD)


# 选择邮箱（这里选择收件箱）
mail.select("inbox")

# 搜索所有未读邮件
status, messages = mail.search(None, '(UNSEEN FROM "export-noreply@mail.notion.so")')

print("登录邮箱", status)

# 获取邮件ID列表
mail_ids = messages[0].split()


# 如果有未读邮件
if mail_ids:
    # 获取最新的一封未读邮件的ID
    latest_email_id = mail_ids[-1]

    # 获取邮件内容（RFC822格式）
    status, msg_data = mail.fetch(latest_email_id, "(RFC822)")

    # 解析邮件内容
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            email_subject, encoding = decode_header(msg["subject"])[0]
            if isinstance(email_subject, bytes):
                email_subject = email_subject.decode(encoding if encoding else "utf-8")
            email_from = msg.get("from")
            
            # 输出邮件信息
            print(f"From: {email_from}")
            print(f"Subject: {email_subject}")

            # 如果邮件是多部分的
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    try:
                        body = part.get_payload(decode=True).decode()
                    except:
                        pass
                    if content_type == "text/html" and "attachment" not in content_disposition:
                        # print(f"Body: {body}")
                        download_link = re.search(r'href="(.*?)">here</a>', body).group(1)
                        download_name = download_link.split("Export-")[-1]
                        
                        print("下载文件名", download_name)
                        print("下载链接", download_link)

                        mail.store(latest_email_id, '+FLAGS', '\\Seen')
                        
                        with requests.get(download_link, stream=True, headers={'cookie': f'file_token={NOTION_FILE_TOKEN}'}) as r:
                            with open(f"uploads/{download_name}", 'wb') as f:
                                shutil.copyfileobj(r.raw, f)
                        
                        blog_copy_replace_file.process("uploads", download_name)
                        
            
            
            # else:
            #     # 处理非多部分邮件
            #     body = msg.get_payload(decode=True).decode()
            #     print(f"Body: {body}")
else:
    print("没有导出的新邮件") 

# 登出
mail.logout()
