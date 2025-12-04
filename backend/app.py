from flask import Flask, request, jsonify
from flask_socketio import SocketIO, send, emit
from flask_cors import CORS
import numpy as np
import os
from model import train_model_and_save, predict_image
import base64
from pdf2image import convert_from_path, convert_from_bytes
import io
from PIL import Image
from werkzeug.utils import secure_filename
from database import Database

app = Flask(__name__)

# Habilitar CORS en la aplicación Flask
CORS(app)

# Carpeta donde se guardarán las imágenes subidas
UPLOAD_FOLDER = './uploads'
DB_FILE = "./formatos.db"
POPPLER_PATH = "..\\poppler-24.02.0\\Library\\bin"
#POPPLER_PATH = "C:\\Program Files\\poppler-24.02.0\\Library\\bin"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
socketio = SocketIO(app, cors_allowed_origins="*")

# Asegúrate de que la carpeta de subida exista
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

db = Database()

@app.route('/', methods=['POST', "PUT", "GET"])
def upload_format():
  if (request.method != "GET"):
    files = request.files.getlist("files")
    form_data = request.form.to_dict()
    name = form_data.get('name')

    coordinates = np.array([form_data.get("fixedCoordinates").split(",")]).reshape(-1,9) if form_data.get("fixedCoordinates") else []
    columns = np.array([form_data.get("columns").split(",")]).reshape(-1,9) if form_data.get("columns") else []

    id = -1
    if (request.method == "POST"):
      height = int(form_data.get("height"))
      width = int(form_data.get("width"))
      id = db.make_db_action(db.insert_format, None, (name, height, width))
    else:
      id = db.make_db_action(db.get_formatid_by_name, None, name)
    
    if len(coordinates):
      coordinates = np.insert(coordinates, coordinates.shape[1], id, 1)
    
    if len(columns):
      columns = np.insert(columns, columns.shape[1], id, 1)

    newColumnsTuple = [c[8] for c in columns]
    oldColumns = db.make_db_action(db.get_columns_by_format, None, id)
    deleteColumns = [column for column in oldColumns if column[5] not in newColumnsTuple]

    newCoordinatesTuple = [c[8] for c in coordinates]
    oldCoordinates = db.make_db_action(db.get_coordinates_by_format, None, id)
    deleteCoordinates = [coordinate for coordinate in oldCoordinates if coordinate[4] not in newCoordinatesTuple]


    for i, col in enumerate(deleteColumns):
      db.make_db_action(db.delete_column_by_field, None, col[5], id)

    for i, coord in enumerate(deleteCoordinates):
      db.make_db_action(db.delete_coordinate_by_field, None, coord[4], id)
      
    for i,coord in enumerate(coordinates):
      db.make_db_action(db.insert_coordinate, None, coord[1:])
      
    for i,coord in enumerate(columns):
      db.make_db_action(db.insert_column, None, coord[1:])
    
    file_path = os.path.join(UPLOAD_FOLDER, name)
    if not os.path.exists(file_path):
      os.makedirs(file_path)
    delete_images = [f for f in os.listdir(file_path) if f.endswith(".png") or f.endswith(".jpg")]

    for file in files:
      filename = secure_filename(file.filename)
      image_filename = os.path.join(file_path, filename)
      if filename in delete_images:
        delete_images.remove(filename)
      file.save(image_filename)

    for file in delete_images:
      os.remove(os.path.join(file_path, file))

    return jsonify({"message": "Files and data successfully uploaded", "id": id}), 200
  else:
    result = db.make_db_action(db.get_formats, None)

    return jsonify({"status": "success", "payload": result}), 200

@app.route('/pdfs', methods=['POST'])
def upload_files():
    files = request.files.getlist('files')
    results = []

    for file in files:
        filename = file.filename
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Convert PDF to images
        images = convert_from_path(filepath, poppler_path=POPPLER_PATH)
        
        for i, image in enumerate(images):
          resized_image = image.resize((1240, 1750))
                
          image_io = io.BytesIO()
          resized_image.save(image_io, format='PNG')
          encoded_img = base64.b64encode(image_io.getvalue()).decode('utf-8')
          
          image_filename = f"{filename.replace('.pdf', '')}_page_{i + 1}.png"
          results.append([image_filename, f"data:image/png;base64,{encoded_img}"])

        os.remove(filepath)

    return jsonify(results)

@app.route('/test', methods=['POST'])
def test():
  file = request.files["file"]
  pdf_bytes = file.read()
  image = convert_from_bytes(pdf_bytes, poppler_path=POPPLER_PATH)[0].resize((1240, 1750))
  image.save("./test.png", format="PNG")

  form_data = request.form.to_dict()
  format = list(form_data.get('format').split(","))
  columns = db.make_db_action(db.get_columns_by_format, None, format[0])
  coordinates = db.make_db_action(db.get_coordinates_by_format, None, format[0])
  filas_roi = db.make_db_action(db.get_rows_roi_id, None, format[0])
  coordinates = [coordinate for coordinate in coordinates if not coordinate[7]]
  
  modelPath = os.path.join(UPLOAD_FOLDER, format[1], f"{format[1]}_model.h5")
  results = predict_image(np.array(image), modelPath, columns, coordinates, filas_roi, False, True, format[1])

  return jsonify({"status": "success", "payload": results}), 200
  

@app.route('/formats', methods=['GET'])
def get_formats_info():
  result = db.make_db_action(db.get_formats, None, False)

  formats = []
  for i,format in enumerate(result):
    image_files = [os.path.join(UPLOAD_FOLDER, f) for f in os.listdir(os.path.join(UPLOAD_FOLDER, format[1])) if f.endswith('.png') or f.endswith(".jpg")]
    formats.append([*format, len(image_files)])
     

  return jsonify({"status": "success", "payload": formats}), 200
  

@app.route("/<id>", methods=["PUT", "GET"])
def change_format_state(id):
  if (request.method == "PUT"):
    db.make_db_action(db.update_format_state, None, id)
    return jsonify({"status": "success"})
  else:
    result = db.make_db_action(db.get_format, None, id)
    columns = db.make_db_action(db.get_columns_for_editing, None, id)
    coordinates = db.make_db_action(db.get_coordinates_by_format, None, id)

    format = result[0][1]
    images_dir = os.path.join(UPLOAD_FOLDER, format)

    image_files = [f for f in os.listdir(images_dir) if os.path.isfile(os.path.join(images_dir, f)) and (f.endswith(".png") or f.endswith("jpg"))]

    data_urls = []
    for image_file in image_files:
        image_path = os.path.join(images_dir, image_file)
        with open(image_path, "rb") as img:
            encoded_string = base64.b64encode(img.read()).decode('utf-8')
            data_url = f"data:image/jpeg;base64,{encoded_string}"
            data_urls.append([image_file, data_url])

    return jsonify({"status": "success", "payload": [coordinates, columns, data_urls, format]}), 200

@app.route("/emails", methods=["GET", "POST"])
def get_emails():
  if (request.method == "GET"):
    result = db.make_db_action(db.get_emails, None)
    return jsonify({"status": "success", "payload": result})
  else:
    data = request.get_json().values()
    db.make_db_action(db.insert_email, None, data)
    return jsonify({"status": "success"})
  
  
@socketio.on('train')
def train_row_model(name):
  file_path = os.path.join(UPLOAD_FOLDER, name)
  train_model_and_save(file_path, file_path, name, emit=emit, request=request, socketio=socketio)



if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', debug=True, port=3000)
