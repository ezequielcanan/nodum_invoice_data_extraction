import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.models import load_model
import pytesseract
import numpy as np
import cv2
import os
import io
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from database import Database


#os.environ['TESSDATA_PREFIX'] = r'C:\Program Files\Tesseract-OCR\tessdata'
os.environ['TESSDATA_PREFIX'] = r'..\Tesseract-OCR\tessdata'
os.environ["TF_ENABLE_ONEDNN_OPTS"] = '0'
#pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
pytesseract.pytesseract.tesseract_cmd = r'..\Tesseract-OCR\tesseract.exe'
DB_FILE = "./formatos.db"
db = Database()

height = 128
width = 128
# Función para cargar y preprocesar la imagen
def to_image(file, path=False, buffer=False):
  if buffer:
     return file
  if path:
    return cv2.imread(file)
  else:
    in_memory_file = io.BytesIO()
    file.save(in_memory_file)
    in_memory_file.seek(0)
    data = np.frombuffer(in_memory_file.getvalue(), dtype=np.uint8)

    # Decode the image data using OpenCV
    image = cv2.imdecode(data, cv2.IMREAD_COLOR)
    return image

def load_and_preprocess_image(filepath, filas_roi, path=True, buffer=False):
    image = to_image(filepath, path, buffer)
    image = image[filas_roi[0]:filas_roi[1], filas_roi[2]:filas_roi[3]]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Binarización adaptativa
    image = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    #image = cv2.GaussianBlur(image, (5, 5), 0)
    #image = cv2.Canny(image, 50, 150, apertureSize=3)

    # Aplicar dilatación seguida de erosión (morfología de cierre)
    image = cv2.blur(image, (350,5)) # antes era 1000 de blur
    laplaciano = cv2.Laplacian(image, cv2.CV_64F)

    # Convertir los valores absolutos a uint8
    laplaciano = np.uint8(np.absolute(laplaciano))

    # Encontrar los contornos usando los bordes detectados
    contornos, _ = cv2.findContours(laplaciano, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Dibujar los contornos en la imagen original
    image = cv2.drawContours(image, contornos, -1, (0, 255, 0), 2)

    image = cv2.blur(image, (20,1))

    #kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 2))  # Ajustar el tamaño según sea necesario

    # Aplicar dilatación seguida de erosión (morfología de cierre)

    # Mostrar la imagen con contornos
    '''cv2.imshow('Contours', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()'''
    '''cv2.imshow('Processed Image', image)
    cv2.waitKey(0)
    cv2.destroyAllWindows()'''
    image = cv2.resize(image, (width, height))  # Redimensionar a un tamaño fijo para la CNN
    image = image / 255.0  # Normalizar los valores de los píxeles
    return image

def load_labels(filepath):
    # Cargar etiquetas desde un archivo .npy
    return np.load(filepath, allow_pickle=True)

# Definir la arquitectura de la CNN
def create_model(input_shape, num_boxes):
    inputs = tf.keras.Input(shape=input_shape)

    # CNN simple
    x = layers.Conv2D(32, (3, 3), activation='relu')(inputs)
    x = layers.MaxPooling2D((2, 2))(x)
    x = layers.Conv2D(64, (3, 3), activation='relu')(x)
    x = layers.MaxPooling2D((2, 2))(x)
    x = layers.Conv2D(128, (3, 3), activation='relu')(x)
    x = layers.MaxPooling2D((2, 2))(x)
    x = layers.Flatten()(x)

    # Fully connected layers
    x = layers.Dense(256, activation='relu')(x)
    x = layers.Dense(128, activation='relu')(x)
    
    # Salida para los bounding boxes
    outputs = layers.Dense(num_boxes * 5)(x)  # num_boxes * 4 (x, y, w, h) para cada bounding box

    model = models.Model(inputs, outputs)
    return model

def train_model_and_save(images_path, labels_path, name, emit, request, socketio):
  rows = list(db.make_db_action(db.get_format_rows, None, name))
  rows = [list(row) for row in rows]
  filas_roi = db.make_db_action(db.get_rows_roi, None, name)

  image_names = [f for f in os.listdir(images_path) if f.endswith('.png') or f.endswith(".jpg")]
  key_index = {key: index for index, key in enumerate(image_names)}

  # Ordenar data basado en el índice del último elemento en cada sublista
  for i, row in enumerate(rows):
    rows[i][0] = row[0] - filas_roi[2]
    rows[i][1] = row[1] - filas_roi[0]

  labels = sorted(rows, key=lambda x: key_index[x[-3]])
  labels = [np.array([*item[0:4], item[-3]]) for item in labels]
  image_labels_object = {}
  for i, label in enumerate(labels):
    img = label[-1]
    if not (img in image_labels_object):
      image_labels_object[img] = []
    image_labels_object[img].append([*label[0:4], 100])
  
  labels = []
  for value in image_labels_object.values():
    labels.append(np.array(value).flatten())

  num_boxes = 10
  image_dir = images_path
  image_files = [os.path.join(image_dir, f) for f in os.listdir(image_dir) if f.endswith('.png') or f.endswith(".jpg")]
  images = np.array([np.array(load_and_preprocess_image(f, filas_roi)) for f in image_files])
  

  images_expanded = np.expand_dims(images, axis=-1)
  labels_expanded = np.array([np.pad(lbl, (0, num_boxes*5 - len(lbl)), 'constant') for lbl in labels], dtype=object).astype(float)
  model = create_model((height, width, 1), num_boxes)

  model.compile(optimizer='adam', loss='mean_squared_error')
  global completed
  completed = False

  global canceled
  canceled = False
  global save
  save = False

  @socketio.on('cancel_training', namespace='/')
  def cancel():
    global canceled
    canceled = True

  @socketio.on('save', namespace='/')
  def cancel():
    global save
    save = True

  while not completed and not canceled:
    history = model.fit(images_expanded, labels_expanded, epochs=1, batch_size=32)
    loss = history.history['loss'][0]
    emit("loss", loss, to=request.sid)
    if loss < 0.15 or save:
        modelPath = os.path.join(images_path, name + "_model.h5")
        if os.path.exists(modelPath):
          os.remove(modelPath)
        model.save(modelPath)
        completed = True if not save else False
        save = False

  if not canceled:
    emit("completed", True)

  return model


def apply_roi_filters(roi):
  gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
  _, binary_roi = cv2.threshold(gray_roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
  return binary_roi
  
def apply_roi_filters_for_quantity(roi,
                                   scale: int = 3,
                                   clahe_clip: float = 3.0,
                                   clahe_grid: tuple = (8, 8),
                                   blur_ksize: tuple = (1, 1),
                                   force_invert: bool = True) -> np.ndarray:

    if roi is None:
        raise ValueError("El parámetro roi no puede ser None")

    roi = roi.astype(np.uint8)

    if roi.ndim == 3 and roi.shape[2] == 4:
        roi = cv2.cvtColor(roi, cv2.COLOR_BGRA2BGR)

    if roi.ndim == 3 and roi.shape[2] == 3:
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    elif roi.ndim == 2:
        gray = roi.copy()
    else:
        raise ValueError("Formato de roi no soportado (esperado grayscale, BGR o BGRA)")

    if scale != 1 and scale > 0:
        new_w = int(gray.shape[1] * scale)
        new_h = int(gray.shape[0] * scale)
        gray = cv2.resize(gray, (new_w, new_h), interpolation=cv2.INTER_CUBIC)

    # CLAHE
    clahe = cv2.createCLAHE(clipLimit=clahe_clip, tileGridSize=clahe_grid)
    gray_clahe = clahe.apply(gray)

    # Suavizado
    blur = cv2.GaussianBlur(gray_clahe, blur_ksize, 0)

    # Binarización con Otsu
    _, bw = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # Asegurar texto en blanco y fondo en negro
    if force_invert:
        if np.mean(bw) > 127:
            bw = 255 - bw
    else:
        bw = (bw > 127).astype(np.uint8) * 255

    return bw

distinctColumns2Lines = ["numero_viaje", "op", "icl", "fec_despacho"]
distinctColumns3LinesFirst = ["icl_precio", "b_porcentaje"]
distinctColumns3LinesSecond = ["numero_viaje", "op", "fec_despacho"]

def predict_image(filepath, modelPath, columns, coordinates, filas_roi, path=False, buffer=True, formato=None):
  imageBuffer = to_image(filepath, path, buffer)
  image = load_and_preprocess_image(imageBuffer, filas_roi, False, True)
  model = load_model(modelPath)
  predicted_boxes = model.predict(np.array([image]))
  valid_coords = np.array(predicted_boxes[0])
  num_boxes = (len(valid_coords) // 5) * 5
  # Recortar el array para que su tamaño sea múltiplo de 5
  valid_coords = valid_coords[:num_boxes]
  # Dividir el array recortado en subarrays de 5 elementos
  boxes = valid_coords.reshape(-1, 5)
  # Print the equal parts
  features = []
  for box in boxes:
      if box[4] > 50:
        features.append(box)

  default_config = r'--oem 3 --psm 6'
  custom_config = default_config
  fmt = (formato or "").upper()
  results = {}
  rows = []
  original_image = imageBuffer
  original_img_height, original_img_width, _ = original_image.shape
  lastY = 0
  
  for i, box in enumerate(features):
    x, y, w, h, _ = box
    x, y, w, h = abs(int(x)), abs(int(y)), abs(int(w)), abs(int(h))
    roi = original_image[filas_roi[0]:filas_roi[1], filas_roi[2]:filas_roi[3]][lastY:lastY+h, 0:filas_roi[3] - filas_roi[2]]
    if not i:
      lastY = h
    else:
      lastY += h
    '''plt.imshow(cv2.cvtColor(roi, cv2.COLOR_BGR2RGB))
    plt.savefig(f'output{i}.png')'''
    img_height, img_width, _ = roi.shape
    values = {}

    lastX = 0
    for z,column in enumerate(columns):
      if (img_width > 10 and img_width > 10):
        try:
            xcol = column[0]
            xcol = int(xcol) - filas_roi[2]
            xnextcol = int(columns[z+1][0] if (z < len(columns) - 1) else img_width)
            fieldname = column[5]
          #if (xnextcol - xcol > 5):
            if fmt == "YPF_2":
              if fieldname not in distinctColumns2Lines:
                field = roi[0:int(img_height/2), xcol:int(column[1])+xcol]
              else:
                field = roi[int(img_height/2):img_height, xcol:int(column[1])+xcol]
            elif fmt == "YPF_3":
              if fieldname in distinctColumns3LinesFirst:
                field = roi[int(img_height/3):int(img_height/3)*2, xcol:int(column[1])+xcol]
              elif fieldname in distinctColumns3LinesSecond:
                field = roi[int(img_height/3)*2:img_height, xcol:int(column[1])+xcol]
              else:
                field = roi[0:int(img_height/3), xcol:int(column[1])+xcol]
            else:
              field = roi[0:img_height, xcol:int(column[1])+xcol]
            
            if (fieldname == "aduana" or fieldname == "lote" or fieldname == "cod_articulo" or fieldname == "observaciones"):
              '''plt.imshow(cv2.cvtColor(field, cv2.COLOR_BGR2RGB))
              plt.title(f"ROI {i}")
              plt.show()'''
              field = apply_roi_filters(field)
               
            elif (fieldname == "cantidad"):
              #print("cantidad")
              field = apply_roi_filters_for_quantity(field)
              #cv2.imwrite(f"roi_{i}_{fieldname}.png", field)
              
            
            if fmt == "ALPEK" and fieldname == "cod_articulo":
                pass
                #custom_config = r'--oem 0 --psm 8 '
            elif (fieldname == "aduana"):
              custom_config = r"--psm 10"
            #elif (fieldname=="precio"):
             # custom_config = r"--oem 3 --psm 12"
            elif (fieldname=="cantidad"):
              if (fmt == "RAIZEN"):
                custom_config = r"--oem 1 --psm 6" # psm 6 para doble linea
              else: 
                custom_config = r"--oem 1 --psm 7" 
            else:
              custom_config = r'--oem 3 --psm 6'
            text = pytesseract.image_to_string(field, lang="spa", config=custom_config)
            text = text.replace("\n", " ").strip().strip("~")
            if fieldname == "aduana" and text == "o":
              text = "0"
            #if fieldname == "precio" or fieldname == "cantidad" or fieldname == "porc_bonif" or fieldname == "imp_desc" or fieldname == "imp_stot_mo":
              #text = text.replace(".", "").replace(",", "")
              #text = text[:-2] + "." + text[-2:]
            values[fieldname] = text
        except Exception as e:
          print("ERROR", e)
          pass
      '''plt.imshow(cv2.cvtColor(field, cv2.COLOR_BGR2RGB))
      plt.savefig(f'f{z}.png')'''
    
    #if round(int(values["imp_stot_mo"]) / int(values["precio"])) !=
    rows.append(values)
  
  for i, box in enumerate(coordinates):
    x, y, w, h, fieldname, _ = box[0:6]
    if (fieldname != "filas"):
      x, y, w, h = int(x), int(y), int(w), int(h)

      roi = original_image[y:y+h, x:x+w]
      if (fieldname == "razon_social"):
        roi = apply_roi_filters(roi)

      try:
        header_config = default_config  # r'--oem 3 --psm 6'
        text = pytesseract.image_to_string(roi, lang="spa", config=header_config)
        results[fieldname] = text.replace("\n", " ").strip()
      except:
        pass
  return (results, rows) if features else [results,]
