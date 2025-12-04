from datetime import datetime
import os, time, re
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
from log import *
import numpy as np


def _parse_alpek_dir_tit(raw: str):
    if not raw:
        return None, None, None, None

    txt = " ".join(str(raw).split())

    #Fecha Vto
    m_vto = re.search(r"Fecha\s*VTO\s*:?\s*(\d{2}/\d{2}/\d{4})", txt, flags=re.IGNORECASE)
    fec_vto = m_vto.group(1) if m_vto else None

    #Nro OC
    m_oc = re.search(r"Numero\s+Pedido\s+Cliente\s*:\s*OC\s*(\d+)", txt, flags=re.IGNORECASE)
    orden_compra = m_oc.group(1) if m_oc else None

    #Cond de Pago
    m_cond = re.search(r"Condiciones\s+de\s+Pago\s*:\s*(.+)$", txt, flags=re.IGNORECASE)
    cond_fpago = m_cond.group(1).strip() if m_cond else None

    #Dirección
    left = txt[:m_vto.start()].strip() if m_vto else txt
    left = re.sub(r"^\s*Entregado\s+en\s*", "", left, flags=re.IGNORECASE)
    if re.match(r"^\s*DEPOSITO\b", left, flags=re.IGNORECASE):
        parts = re.split(r"\s{2,}", left.strip(), maxsplit=1)
        if len(parts) == 2:
            left = parts[1]
        else:
            left = re.sub(r"^\s*DEPOSITO\b\s*", "", left, flags=re.IGNORECASE)
    left = re.sub(r"^[A-ZÁÉÍÓÚÑ0-9\.\-&/ ]*?(?:S\.A\.|S\.R\.L\.|S\.A\.I\.C\.)\s+", "", left)
    street_anchor = re.search(
        r"\b(AV\.?|AVDA\.?|AVENIDA|AV\.?\s*PTE|PTE\.?|PRESIDENTE|CALLE|CAMINO|BV\.?|BULEVAR|RUTA|RN|RP)\b",
        left,
        flags=re.IGNORECASE
    )
    start_idx = street_anchor.start() if street_anchor else None
    if start_idx is None:
        name_number = re.search(r"[A-ZÁÉÍÓÚÑ][A-ZÁÉÍÓÚÑ\.\- ]+?\s+\d{1,6}\b", left)
        if name_number:
            start_idx = name_number.start()
    if start_idx is None:
        km_match = re.search(r"\bKM\b", left, flags=re.IGNORECASE)
        if km_match:
            start_idx = km_match.start()
    if start_idx is None:
        start_idx = 0
    end_idx = None
    m_arg = re.search(r"\bARGENTINA\b", left, flags=re.IGNORECASE)
    if m_arg:
        end_idx = m_arg.end()
    dir_base = left[start_idx:end_idx].strip() if end_idx else left[start_idx:].strip()
    dir_base = " ".join(dir_base.split()) if dir_base else None

    return (dir_base or None, fec_vto, orden_compra, cond_fpago or None)

load_dotenv()
dir_origen = os.getenv("DIR_ORIGEN")
dir_destino = os.getenv("DIR_DESTINO")

db = Database()
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
          log_debug("IF .PDF", "Files")
          self.file_dir = os.path.abspath(os.path.join(os.path.join(new_file, os.pardir), file_name))
          log_info(f"Archivo Nuevo: \"{self.file_dir}\"", "Files")
          self.parent =self.getParentFolder(self.file_dir)
          try:
            pdf_bytes = self.pdf_to_bytes(self.file_dir)
            #pdf_bytes = part.get_payload(decode=True)
          except:
            log_error("Error leyendo los bytes del PDF", "Files")
          try:
            body = self.convert_pdf_to_images(pdf_bytes, self.file_dir, self.parent)
          except IOError:
            log_error(f"Error procesando el archivo: \"{self.file_dir}\"", "Files")
            type, value, traceback = sys.exc_info()
            log_error('Error opening %s: %s' % (value.filename, value.strerror), "Files")
      except IOError:
            log_error("Error procesando el archivo nuevo", "Files")
            type, value, traceback = sys.exc_info()
            log_error('Error opening %s: %s' % (value.filename, value.strerror), "Files")
        
  def on_created(self, event):
    log_info(str(datetime.now()) + " " + str(event), "Files")
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
    
  def getParentFolder(self, path: str) -> str:
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
    if allparts[-2] != None:
       return allparts[-2].strip().upper()
    else:
      return allparts[-2]

  def processData(self, data: dict[str,str], formato: str) -> dict:
    for key, value in data.items():
      if "'" in value:
         data[key] = value.replace("'","`")
      if "fec_" in key:
         data[key] = value.replace(".","/")
      elif "nro_dgi" in key:
         data[key] = ''.join(re.findall(r'\d+', value))
      elif key == "cond_IVA":
         data[key] = value.replace("I1VA ","IVA ").replace("1.V.A. ","IVA ").replace("1VA ","IVA ") 
      elif key == "porc_iva":
         data[key] = value.replace("%","").strip() 
      elif key == "serie_docum" and formato == "ALPEK":
         data[key] = value.split("-",1)[0]
      elif key == "nro_docum" and formato == "ALPEK":
         right = value.split("-",1)[1] if "-" in value else value
         digits = ''.join(ch for ch in right if ch.isdigit())
         data[key] = digits.zfill(8)
    if formato == "ALPEK" and "dir_tit" in data:
       dir_limpio, fec_vto, oc, cond_pago = _parse_alpek_dir_tit(data.get("dir_tit", ""))
       data["dir_tit"] = dir_limpio if dir_limpio else None
       data["fec_vencimiento"] = fec_vto if fec_vto else None
       data["orden_compra"] = oc if oc else None
       data["cond_fpago"] = cond_pago if cond_pago else None
     
    data.update({'formato': formato})

    return data
    
    
  def processDetalle(self, data: dict[str,str], formato: str) -> dict:
    for key, value in data.items():
      #if "'" in value:
       #  data[key] = value.replace("'","`")
      if "cantidad" == key:
         data[key] = value.split(" ", 1)[0]
      elif "cod_unidad" == key:
         data[key] = value.split(" ", 1)[0]
      elif "precio" == key:
         data[key] = value.split(" ", 1)[0]
      elif "cod_articulo" == key and formato == "RAIZEN":
         s = (value or "").strip()
         if s and not s.startswith("Q"):
            data[key] = "Q" + s
         else:
            data[key] = s
      elif "nom_articulo" == key and formato == "RAIZEN":
         data[key] = value.split("Producto", 1)[0]
      elif "cod_articulo" == key and formato == "YPF":
         data[key] = value.split(" ", 1)[0]
      elif "numero_viaje" == key and formato == "YPF":
         match = re.search(r"\b\d{4}R\d{8}\b", value)
         if match:
            data[key] = match.group(0)
         else:
            data[key] = value.strip()
      elif key == "nom_articulo" and formato == "YPF":
         if "ICL" in value:
            data[key] = value.split("ICL", 1)[0].strip()
         else:
            m = re.search(r"\d+", value)
            data[key] = (value[:m.start()] if m else value).strip()
    return data

  def convert_pdf_to_images(self, pdf_bytes, original_file_name, formato):
    log_debug("Creando PDF temporal...", "Files")
    temp_pdf_path = os.path.join(self.dir_destino, 'temp.pdf')
    with open(temp_pdf_path, 'wb') as temp_pdf_file:
        temp_pdf_file.write(pdf_bytes)

    log_debug("Convirtiendo el PDF a JPG", "Files")
    pdf_document = convert_from_bytes(pdf_bytes, poppler_path=POPPLER_PATH)
    base_name = os.path.splitext(original_file_name)[0]
    rows = []
    data: dict = 0
    #download_f = os.path.join(self.dir_origen, formato)
    for page_num, image in enumerate(pdf_document):
      log_debug("Leyendo los Datos... 1", "Files")
      page = image.resize((1240, 1750))
      
      if not os.path.exists(self.dir_destino):
        os.makedirs(self.dir_destino)

      image_path = os.path.join(self.dir_destino, f'{base_name}_page_{page_num+1}.jpg')
      page.save(image_path)
      log_debug("Leyendo los Datos... 2", "Files")
      email_format = db.make_db_action(db.get_format_name, "Files", formato)
      log_debug("Leyendo los Datos... 3", "Files")
      filas_roi = db.make_db_action(db.get_rows_roi_id, "Files", email_format[0][0])
      log_debug("Leyendo los Datos... 4", "Files")
      image = Image.open(image_path)
      if not len(email_format):
        return f"No existe el formato asociado: {formato}"
      else:
        coordinates, columns = db.make_db_action(db.get_predict_data, "Files", email_format[0][0])
        model_path = os.path.join(UPLOAD_FOLDER, email_format[0][1], f'{email_format[0][1]}_model.h5')
        log_debug("Leyendo los Datos... 5", "Files")
        result = predict_image(np.array(page),model_path,columns,coordinates,filas_roi,False,True, formato=formato)
        print(result)
        if not result:
          return f"La factura recibida no concuerda con el modelo: {formato}"
        if page_num:
          new_data = result[0]
          data = new_data if new_data["nro_docum"] == data["nro_docum"] else data
          if "hoja" in new_data:
            if len(result) > 1: 
              if data["hoja"] == new_data["hoja"]:
                rows.append(result[1])
        else:
          if len(result) > 1:
            rows.append(result[1])

        if not data:
          print(result[0])
          data = self.processData(result[0], formato)
        log_debug(data, "Files")

    rows = self.flatten(rows)

    log_debug("Grabando Datos de la Factura...", "Files")
    id = db.make_db_action(db.insert_factura, "Files", data)
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
    
    db.make_db_action(db.update_factura, "Files", id, "thumbnail", pdf_path)
    
    for i in range(len(rows)):
        rows[i] = self.processDetalle(rows[i], formato)
    db.make_db_action(db.insert_detalles, "Files", rows)
    log_info(f"Fin Inserts: {original_file_name}", "Files")
    if os.path.exists(original_file_name):
      try:
        os.remove(original_file_name)
      except IOError:
        log_error(f"Error boorando el archivo: \"{self.file_dir}\"", "Files")
        type, value, traceback = sys.exc_info()
        log_error('Error opening %s: %s' % (value.filename, value.strerror), "Files")
    else:
      log_info(f"The file {original_file_name} does not exist", "Files") 


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
  log_file("Files")
  log_info("Monitoring started", "Files")
  
  try:
      while True:
          #event_handler.process_emails()
          time.sleep(20)
  except KeyboardInterrupt:
      log_info('Interrupción recibida, cerrando conexión...', "Files")
