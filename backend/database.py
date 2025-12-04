import pyodbc
import sqlite3
from datetime import datetime
from log import *

server = 'WM-WIN64-NDMDEV'
database = 'NODUM_FP'
username = 'ecanan'
password = 'SOL07piedra'
connection_string = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'

ENVIRONMENT = "PROD"
isEnvDev = ENVIRONMENT == "DEV"
class Database():
  def __init__(self, file="./formatos.db"):
    self.file = file
  
  def make_db_action(self, func, log: str, *args):
    conn = 0
    if isEnvDev:
      conn = sqlite3.connect(self.file)
    else:
      conn = pyodbc.connect(connection_string)
    cur = conn.cursor()
    if log is not None:
      log_debug("DB, Conectado a DB", log)
    result = func(cur, log, *args)
    if log is not None:
      log_debug("DB, Funcion Ejecutada", log)
    conn.commit()
    conn.close()
    return result

  def get_emails(self, cur, log: str):
    if log is not None:
      log_debug("SELECT * FROM emails", log)
    cur.execute("SELECT * FROM emails")
    return cur.fetchall()
  
  def get_email(self, cur, log: str, email):
    if log is not None:
      log_debug(f"SELECT * FROM emails WHERE email = '{email}'", log)
    cur.execute("SELECT * FROM emails WHERE email = ?", (email,))
    return cur.fetchall()

  def get_format(self, cur, log: str, format):
    if log is not None:
      log_debug(f"SELECT * FROM formatos WHERE id = {format}", log)
    cur.execute("SELECT * FROM formatos WHERE id = ?", (format,))
    return cur.fetchall()

  def get_format_name(self, cur, log: str, format):
    if log is not None:
      log_debug(f"SELECT * FROM formatos WHERE UPPER(TRIM(name)) = '{format}'", log)
    cur.execute("SELECT * FROM formatos WHERE UPPER(TRIM(name)) = ?", (format,))
    return cur.fetchall()

  def get_predict_data(self, cur, log: str, format):
    if log is not None:
      log_debug(f"SELECT * FROM coordenadas WHERE formato = {format} AND isRow = 0", log)
      log_debug(f"SELECT * FROM columns WHERE formato = {format}", log)
    cur.execute("SELECT * FROM coordenadas WHERE formato = ? AND isRow = 0", (format,))
    coordinates = cur.fetchall()
    cur.execute("SELECT * FROM columns WHERE formato = ?", (format,))
    return (coordinates, cur.fetchall())
  
  def from_dic_to_sql_data(self, data):
    fields = ', '.join(data.keys())
    num_fields = ', '.join('?' * len(data))
    values = tuple(data.values())
    return (fields, num_fields, values)
  
  def from_dic_to_sql_data_date(self, data):
    fields = ', '.join(tuple(data.keys()))
    num_fields = ', '.join('?' * (len(data)+1))
    now = datetime.now()
    val =  list(data.values())
    val.append(now.strftime("%Y-%m-%d %H:%M:%S")+(now.strftime(":%f"))[:4])
    values = tuple(val)
    return (fields, num_fields, values)

  def insert_factura(self, cur, log: str, data):
    fields, num_fields, values = self.from_dic_to_sql_data_date(data)
    if log is not None:
      log_info( f"INSERT INTO facturas ({fields}, datetime) OUTPUT INSERTED.id VALUES {values}", log)
    cur.execute(f"INSERT INTO facturas ({fields}, datetime) OUTPUT INSERTED.id VALUES ({num_fields})", values)
    return cur.fetchone()[0]
      

  def insert_detalles(self, cur, log: str, detalles):
    for i, detalle in enumerate(detalles):
      fields, num_fields, values = self.from_dic_to_sql_data(detalle)
      if log is not None:
        log_info( f"INSERT INTO detalles ({fields}) VALUES {values}", log)
      cur.execute(f'INSERT INTO detalles ({fields}) VALUES ({num_fields})', values)
    return True
  
  def insert_format(self, cur, log: str, data):
    if not isEnvDev:
      name, height, width = data

      if log is not None:
        log_debug(f"""IF EXISTS (SELECT 1 FROM formatos WHERE name = '{name}')
      BEGIN
          UPDATE formatos SET height = {height}, width = {width} WHERE name = '{name}'
      END
      ELSE
      BEGIN
          INSERT INTO formatos (name, height, width) VALUES ('{name}', {height}, {width})
      END""", log)
      cur.execute("""IF EXISTS (SELECT 1 FROM formatos WHERE name = ?)
      BEGIN
          UPDATE formatos SET height = ?, width = ? WHERE name = ?
      END
      ELSE
      BEGIN
          INSERT INTO formatos (name, height, width) VALUES (?, ?, ?)
      END""", (name, height, width, name, name, height, width))
      cur.execute("SELECT id FROM formatos WHERE name = ?", (name, ))
      return cur.fetchone()[0]
    else:
      cur.execute("INSERT OR REPLACE INTO formatos(name, height, width) VALUES(?,?,?)", data)
      return cur.lastrowid
  
  def get_formats(self, cur, log: str, filter=True):
    if log is not None:
      log_debug("SELECT * FROM formatos", log)
    cur.execute("SELECT * FROM formatos")
    if isEnvDev or not filter:
      return cur.fetchall()
    else:
      result = []
      for row in cur.fetchall():
        row_dict = {column[0]: value for column, value in zip(cur.description, row)}
        result.append(list(row_dict.values()))
      return result

  def get_formatid_by_name(self, cur, log: str, name):
    if log is not None:
      log_debug(f"SELECT * FROM formatos WHERE name = '{name}'", log)
    cur.execute("SELECT id FROM formatos WHERE name = ?", (name, ))
    return cur.fetchone()[0]
  
  def get_columns_by_format(self, cur, log: str, id):
    cur.execute("SELECT * FROM columns WHERE formato = ?", (id,))
    return cur.fetchall()
  
  def get_coordinates_by_format(self, cur, log: str, id):
    if log is not None:
      log_debug(f"SELECT * FROM coordenadas WHERE formato = {id}", log)
    cur.execute("SELECT * FROM coordenadas WHERE formato = ?", (id,))
    if isEnvDev:
      return cur.fetchall()
    else:
      result = []
      for row in cur.fetchall():
        row_dict = {column[0]: value for column, value in zip(cur.description, row)}
        result.append(list(row_dict.values()))
      return result

  def get_columns_for_editing(self, cur, log: str, id):
    if log is not None:
      log_debug(f"SELECT originalx AS x, originaly AS y, width, height, field, [file], imageName FROM columns WHERE formato = {id}", log)
    cur.execute("SELECT originalx AS x, originaly AS y, width, height, field, [file], imageName FROM columns WHERE formato = ?", (id,))
    if isEnvDev:
      return cur.fetchall()
    else:
      result = []
      for row in cur.fetchall():
        row_dict = {column[0]: value for column, value in zip(cur.description, row)}
        result.append(list(row_dict.values()))
      return result
  
  def get_emails(self, cur, log: str):
    if log is not None:
      log_debug(f"SELECT * FROM emails", log)
    cur.execute("SELECT * FROM emails")
    if isEnvDev:
      return cur.fetchall()
    else:
      result = []
      for row in cur.fetchall():
        row_dict = {column[0]: value for column, value in zip(cur.description, row)}
        result.append(list(row_dict.values()))
      return result

  def get_format_rows(self, cur, log: str, name):
    if log is not None:
      log_debug(f"SELECT c.* FROM coordenadas c JOIN formatos f ON c.formato = f.id WHERE f.name = '{name}' AND c.isRow = 1", log)
    cur.execute("SELECT c.* FROM coordenadas c JOIN formatos f ON c.formato = f.id WHERE f.name = ? AND c.isRow = 1", (name,))
    return cur.fetchall()

  def get_rows_roi(self, cur, log: str, name):
    if log is not None:
      log_debug(f"SELECT c.* FROM coordenadas c JOIN formatos f ON c.formato = f.id WHERE f.name = '{name}' AND c.field = 'filas'", log)
    cur.execute(    "SELECT c.* FROM coordenadas c JOIN formatos f ON c.formato = f.id WHERE f.name = ? AND c.field = 'filas'", (name,))
    coords = cur.fetchone()
    return (int(coords[1]), int(coords[1]) + int(coords[3]), int(coords[0]), int(coords[0]) + int(coords[2]))
  
  def get_rows_roi_id(self, cur, log: str, name):
    if log is not None:
      log_debug(f"SELECT c.* FROM coordenadas c JOIN formatos f ON c.formato = f.id WHERE f.id = {name} AND c.field = 'filas'", log)
    cur.execute("SELECT c.* FROM coordenadas c JOIN formatos f ON c.formato = f.id WHERE f.id = ? AND c.field = 'filas'", (name,))
    coords = cur.fetchone()
    return (int(coords[1]), int(coords[1]) + int(coords[3]), int(coords[0]), int(coords[0]) + int(coords[2]))
    

  def delete_column_by_field(self, cur, log: str, field, format):
    if log is not None:
      log_debug(f"DELETE FROM columns WHERE field = '{field}' AND formato = {format}", log)
    cur.execute("DELETE FROM columns WHERE field = ? AND formato = ?", (field, format))

  def delete_coordinate_by_field(self, cur, log: str, field, format):
    if log is not None:
      log_debug(f"DELETE FROM coordenadas WHERE field = '{field}' AND formato = {format}", log)
    cur.execute("DELETE FROM coordenadas WHERE field = ? AND formato = ?", (field, format))

  def insert_email(self, cur, log: str, data):
    if not isEnvDev:
      email, value = data

      cur.execute("""
      IF EXISTS (SELECT 1 FROM emails WHERE email = ?)
      BEGIN
          UPDATE emails SET formato = ? WHERE email = ?
      END
      ELSE
      BEGIN
          INSERT INTO emails (email, formato) VALUES (?, ?)
      END
      """, (email, value, email, email, value))
    else:
      cur.execute("INSERT OR REPLACE INTO emails VALUES(?,?)", list(data))

  def insert_coordinate(self, cur, log: str, data):
    if not isEnvDev:
      x, y, width, height, file, imageName, isRow, field, formato = data
      cur.execute("""
      IF EXISTS (SELECT 1 FROM coordenadas WHERE field = ? AND formato = ?)
      BEGIN
          UPDATE coordenadas 
          SET x = ?, y = ?, width = ?, height = ?, [file] = ?, imageName = ?, isRow = ?
          WHERE formato = ? AND field = ?
      END
      ELSE
      BEGIN
          INSERT INTO coordenadas (x, y, width, height, [file], imageName, isRow, field, formato)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      END
      """, (field, formato, x, y, width, height, file, imageName, isRow, formato, field, x, y, width, height, file, imageName, isRow, field, formato))
    else:
      cur.execute("INSERT OR REPLACE INTO coordenadas(x,y,width,height,file,imageName,isRow,field,formato) VALUES(?,?,?,?,?,?,?,?,?)", data)

  def insert_column(self, cur, log: str, data):
    if not isEnvDev:
      x, width, height, originalx, originaly, file, imageName, field, formato = data
      cur.execute("""
      IF EXISTS (SELECT 1 FROM columns WHERE field = ? AND formato = ?)
      BEGIN
          UPDATE columns 
          SET x = ?, width = ?, height = ?, originalx = ?, originaly = ?, [file] = ?, imageName = ?
          WHERE formato = ? AND field = ?
      END
      ELSE
      BEGIN
          INSERT INTO columns (x, width, height, originalx, originaly, [file], imageName, field, formato)
          VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      END
      """, (field, formato, x, width, height, originalx, originaly, file, imageName, formato, field, x, width, height, originalx, originaly, file, imageName, field, formato))
    else:
      cur.execute("INSERT OR REPLACE INTO columns(x,width,height,originalx,originaly,file,imageName,field,formato) VALUES(?,?,?,?,?,?,?,?,?)",data)

  def update_format_state(self, cur, log: str, id):
    if log is not None:
      log_debug(f"UPDATE formatos SET estado = '1' WHERE id = {id}", log)
    cur.execute("UPDATE formatos SET estado = '1' WHERE id = ?", (int(id),))

  def update_factura(self, cur, log: str, id, field, value):
    if log is not None:
      log_debug(f"UPDATE facturas SET {field} = '{value}' WHERE id = {id}", log)
    cur.execute(f"UPDATE facturas SET {field} = ? WHERE id = ?", (value, int(id)))