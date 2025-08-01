import imaplib
import email
import os
import time
from pdf2image import convert_from_bytes
from database import Database
from app import UPLOAD_FOLDER
from app import POPPLER_PATH
import re
from model import predict_image
from PIL import Image
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
from log import Log

load_dotenv()

smtp_server = 'smtp.gmail.com'
smtp_port = 587 
smtp_user = os.getenv("MAIL")
smtp_password = os.getenv("APP_PASSWORD")

db = Database()
logger = Log("Mails")
class EmailAttachmentDownloader:
  def __init__(self, email_account, password, download_folder=os.getenv("DIR_DESTINO")):
      self.imap_server = 'imap.gmail.com'
      self.imap_port = 993
      self.email_account = email_account
      self.password = password
      self.download_folder = download_folder
      
      if not os.path.exists(self.download_folder):
          os.makedirs(self.download_folder)
      
      self.mail = self.connect_to_email()
  
  def connect_to_email(self):
      mail = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
      mail.login(self.email_account, self.password)
      return mail
  
  def fetch_unseen_emails(self):
      self.mail.select('inbox')
      result, data = self.mail.search(None, '(UNSEEN)')
      if result == 'OK':
          return data[0].split()
      return []
  
  def download_and_convert_pdf(self, email_id):
    result, data = self.mail.fetch(email_id, '(RFC822)')
    if result != 'OK':
      logger.info(f"Error fetching email {email_id}")
      return
    
    raw_email = data[0][1]
    msg = email.message_from_bytes(raw_email)
    from_ = msg.get("From")
    email_address = re.search(r'<(.+?)>', from_).group(1) if '<' in from_ else from_
    
    for part in msg.walk():
      if part.get_content_maintype() == 'multipart':
        continue
      if part.get('Content-Disposition') is None:
        continue
      
      file_name = part.get_filename()
      if file_name and file_name.endswith('.pdf'):
        pdf_bytes = part.get_payload(decode=True)
        body = self.convert_pdf_to_images(pdf_bytes, file_name, email_address)
        if body:
          msg = MIMEMultipart()
          msg['From'] = smtp_user
          msg['To'] = 'damiancanan@gmail.com'
          msg['Subject'] = 'Error en el proceso de una factura'

          msg.attach(MIMEText(body, 'plain'))
          try:
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
          except Exception as e:
              logger.info(f"Error al enviar el correo: {e}")
  
  def convert_pdf_to_images(self, pdf_bytes, original_file_name, from_email):
    temp_pdf_path = os.path.join(self.download_folder, 'temp.pdf')
    with open(temp_pdf_path, 'wb') as temp_pdf_file:
        temp_pdf_file.write(pdf_bytes)

        
    pdf_document = convert_from_bytes(pdf_bytes, poppler_path=POPPLER_PATH)
    base_name = os.path.splitext(original_file_name)[0]
    rows = []
    data = 0
    download_f = os.path.join(self.download_folder, from_email.replace("@", "_").replace(".", "_"))
    for page_num, image in enumerate(pdf_document):
      page = image.resize((1240, 1750))
      
      if not os.path.exists(download_f):
        os.makedirs(download_f)

      image_path = os.path.join(download_f, f'{base_name}_page_{page_num+1}.jpg')
      page.save(image_path)
      email_data =  db.make_db_action(db.get_email, from_email)
      if not len(email_data):
        return f"Email no reconocido: {from_email}"
      email_format = db.make_db_action(db.get_format, email_data[0][1])
      filas_roi = db.make_db_action(db.get_rows_roi_id, email_format[0][0])
      image = Image.open(image_path)
      if not len(email_format):
        return f"Este email no tiene un formato asociado: {from_email}"
      else:
        coordinates, columns = db.make_db_action(db.get_predict_data, email_format[0][0])
        model_path = os.path.join(UPLOAD_FOLDER, email_format[0][1], f'{email_format[0][1]}_model.h5')
        result = predict_image(image_path,model_path,columns,coordinates,filas_roi,True,False)
        if not result:
          return f"La factura recibida no concuerda con el modelo: {from_email}"
        if page_num:
          new_data = result[0]
          if "hoja" in new_data:
            if data["hoja"] == new_data["hoja"]:
              rows.append(result[1])
        else:
          rows.append(result[1])

        if not data:
          data = result[0]

    rows = self.flatten(rows)
    id = db.make_db_action(db.insert_factura, data)
    for i,row in enumerate(rows):
      rows[i]["factura"] = id
    
    os.remove(temp_pdf_path)

    pdf_path = os.path.join(download_f, f'{id}.pdf')
    with open(pdf_path, 'wb') as pdf_file:
        pdf_file.write(pdf_bytes)
    
    for page_num, image in enumerate(pdf_document):
      image_path = os.path.join(download_f, f'{base_name}_page_{page_num+1}.jpg')
      new_image_path = os.path.join(download_f, f'{id}_page_{page_num+1}.jpg')
      os.rename(image_path, new_image_path)
    
    db.make_db_action(db.update_factura, id, "thumbnail", pdf_path)
    
    db.make_db_action(db.insert_detalles, rows)
  


  def flatten(self, lst):
    flat_list = []
    for item in lst:
        if isinstance(item, list):
            flat_list.extend(self.flatten(item))
        else:
            flat_list.append(item)
    return flat_list
  
  def mark_as_seen(self, email_id):
      self.mail.store(email_id, '+FLAGS', '\\Seen')
  
  def process_emails(self):
      unseen_emails = self.fetch_unseen_emails()
      for email_id in unseen_emails:
          self.download_and_convert_pdf(email_id)
          self.mark_as_seen(email_id)
  
  def close_connection(self):
      self.mail.logout()

if __name__ == '__main__':
  email_account = smtp_user
  password = smtp_password
  
  downloader = EmailAttachmentDownloader(email_account, password)
  try:
      while True:
          downloader.process_emails()
          time.sleep(20)
  except KeyboardInterrupt:
      logger.info('Interrupción recibida, cerrando conexión...')
  finally:
      downloader.close_connection()
