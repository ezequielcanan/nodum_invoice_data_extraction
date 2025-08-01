from datetime import datetime
import os, time
from pdf2image import convert_from_bytes
from database import Database
from app import UPLOAD_FOLDER
from app import POPPLER_PATH
from os import path
#import re
from model import predict_image
from PIL import Image
from dotenv import load_dotenv
from watchdog.observers import Observer
#from watchdog.events import FileSystemEventHandler
#from watchdog.events import FileCreatedEvent
from watchdog.events import PatternMatchingEventHandler
from log import Log

load_dotenv()
dir_origen = os.getenv("DIR_ORIGEN")
dir_destino = os.getenv("DIR_DESTINO")

db = Database()
logger = Log("Files")
class directoryListener(PatternMatchingEventHandler):
  patterns = ["*.pdf"]
  _ignore_directories = None
  _ignore_patterns = None
  _case_sensitive = None
  def __init__(self):
      self.dir_origen = dir_origen
      self.dir_destino = dir_destino
      
      if not os.path.exists(self.dir_origen):
          os.makedirs(self.dir_origen)
      if not os.path.exists(self.dir_destino):
          os.makedirs(self.dir_destino)
  
  def process(self, event):
      self.dir_origen = dir_origen
      self.dir_destino = dir_destino
      try:
        if not os.path.exists(self.dir_origen):
            os.makedirs(self.dir_origen)
        if not os.path.exists(self.dir_destino):
            os.makedirs(self.dir_destino)
        
        new_file = event.src_path
        file_name = path.basename(new_file)
        if file_name and file_name.endswith('.pdf'):
          self.file_dir = os.path.abspath(os.path.join(os.path.join(new_file, os.pardir), file_name))
          logger.info(f"Archivo Nuevo: \"{self.file_dir}\"")
          self.parent =self.getParentFolder(self.file_dir)
          try:
            pdf_bytes = self.pdf_to_bytes(self.file_dir)
            #pdf_bytes = part.get_payload(decode=True)
          except:
            logger.error(f"Error leyendo los bytes del PDF")
          try:
            body = self.convert_pdf_to_images(pdf_bytes, self.file_dir, self.parent)
          except:
            logger.error(f"Error procesando el archivo: \"{self.file_dir}\"")
      except:
            logger.error(f"Error procesando el archivo nuevo")
        
  def on_created(self, event):
    logger.info(str(datetime.now()) + " " + str(event))
    time.sleep(3)
    self.process(event)

  def on_modified(self, event):
    pass

  def on_moved(self, event):
    pass

  def on_deleted(self, event):
    pass
  
  def pdf_to_bytes(self, pdf_path): 
    with open(pdf_path, 'rb') as pdf_file: 
        byte_array = pdf_file.read() 
    return byte_array 
    
  def getParentFolder(self, path):
    allparts = []
    while 1:
        parts = os.path.split(path)
        if parts[0] == path:  # sentinel for absolute paths
            allparts.insert(0, parts[0])
            break
        elif parts[1] == path: # sentinel for relative paths
            allparts.insert(0, parts[1])
            break
        else:
            path = parts[0]
            allparts.insert(0, parts[1])
    return allparts[-2]
  
  def convert_pdf_to_images(self, pdf_bytes, original_file_name, parent_folder):
    logger.debug(f"Creando PDF temporal...")
    temp_pdf_path = os.path.join(self.dir_destino, 'temp.pdf')
    with open(temp_pdf_path, 'wb') as temp_pdf_file:
        temp_pdf_file.write(pdf_bytes)

    logger.debug(f"Convirtiendo el PDF a JPG")
    pdf_document = convert_from_bytes(pdf_bytes, poppler_path=POPPLER_PATH)
    base_name = os.path.splitext(original_file_name)[0]
    rows = []
    data = 0
    #download_f = os.path.join(self.dir_origen, parent_folder)
    for page_num, image in enumerate(pdf_document):
      logger.debug(f"Leyendo los Datos... 1")
      page = image.resize((1240, 1750))
      
      if not os.path.exists(self.dir_destino):
        os.makedirs(self.dir_destino)

      image_path = os.path.join(self.dir_destino, f'{base_name}_page_{page_num+1}.jpg')
      page.save(image_path)
      logger.debug(f"Leyendo los Datos... 2")
      email_format = db.make_db_action(db.get_format_name, parent_folder.strip().upper(), logger)
      logger.debug(f"Leyendo los Datos... 3")
      filas_roi = db.make_db_action(db.get_rows_roi_id, email_format[0][0], logger)
      logger.debug(f"Leyendo los Datos... 4")
      image = Image.open(image_path)
      if not len(email_format):
        return f"No existe el formato asociado: {parent_folder}"
      else:
        coordinates, columns = db.make_db_action(db.get_predict_data, email_format[0][0], logger)
        model_path = os.path.join(UPLOAD_FOLDER, email_format[0][1], f'{email_format[0][1]}_model.h5')
        logger.debug(f"Leyendo los Datos...")
        result = predict_image(image_path,model_path,columns,coordinates,filas_roi,True,False)
        if not result:
          return f"La factura recibida no concuerda con el modelo: {parent_folder}"
        if page_num:
          new_data = result[0]
          if "hoja" in new_data:
            if data["hoja"] == new_data["hoja"]:
              rows.append(result[1])
        else:
          rows.append(result[1])

        if not data:
          data = result[0]

    logger.debug(f"Grabando Datos de la Factura...")
    rows = self.flatten(rows)
    id = db.make_db_action(db.insert_factura, data, logger)
    for i,row in enumerate(rows):
      rows[i]["factura"] = id
    
    os.remove(temp_pdf_path)

    pdf_path = os.path.join(self.dir_destino, f'{id}.pdf')
    with open(pdf_path, 'wb') as pdf_file:
        pdf_file.write(pdf_bytes)
    
    for page_num, image in enumerate(pdf_document):
      image_path = os.path.join(self.dir_destino, f'{base_name}_page_{page_num+1}.jpg')
      new_image_path = os.path.join(self.dir_destino, f'{id}_page_{page_num+1}.jpg')
      os.rename(image_path, new_image_path)
    
    db.make_db_action(db.update_factura, id, "thumbnail", pdf_path, logger)
    
    db.make_db_action(db.insert_detalles, rows, logger)
    logger.info(f"Fin Inserts: {original_file_name}")


  def flatten(self, lst):
    flat_list = []
    for item in lst:
        if isinstance(item, list):
            flat_list.extend(self.flatten(item))
        else:
            flat_list.append(item)
    return flat_list

if __name__ == '__main__':  
  event_handler = directoryListener()
  observer = Observer()
  observer.schedule(event_handler, path=dir_origen, recursive=True)
  observer.start()
  logger.info("Monitoring started")
  
  try:
      while True:
          #event_handler.process_emails()
          time.sleep(20)
  except KeyboardInterrupt:
      logger.info('Interrupción recibida, cerrando conexión...')
