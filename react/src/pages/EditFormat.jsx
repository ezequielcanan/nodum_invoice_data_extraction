import { useState, useEffect } from "react"
import 'pdfjs-dist/web/pdf_viewer.css';
import customAxios from "../config/axios.config.js";
import { useNavigate, useParams } from "react-router-dom";
import { socket } from "../socket.js";
import { initialFields } from "../utils.js";
import Loader from "../components/Loader.jsx";
import FormatEditing from "../components/FormatEditing.jsx";
import Main from "../containers/Main.jsx";
import Error from "../components/Error.jsx";

const EditFormat = () => {
  const [fields, setFields] = useState([...initialFields.map(f => {return {...f}})])
  const [files, setFiles] = useState([])
  const [name, setName] = useState(null)
  const [rectangles, setRectangles] = useState([])
  const [loading, setLoading] = useState(false)
  const [training, setTraining] = useState(false)
  const [error, setError] = useState(false)
  const { id } = useParams()

  useEffect(() => {
    customAxios.get("/" + id).then((res) => {
      const info = res.data.payload
      const newRectangles = []
      const newFields = []
      info[0].forEach((coord) => {
        const fieldName = coord[4]
        const fieldIndex = fields.findIndex(f => f.field == fieldName)
        const newRectangle = {
          x: coord[0],
          y: coord[1],
          width: coord[2],
          height: coord[3],
          row: coord[7],
          column: false,
          file: coord[5],
          imageName: coord[6],
          field: fieldName
        }
        if (fieldIndex != -1) {
          fields[fieldIndex].completed = true
          newRectangle.text = fields[fieldIndex]?.text
        } else {
          const rowText = `Fila ${fieldName.replace("r", "")}`
          newFields.push({ text: rowText, field: fieldName, completed: true, focused: false, row: true, file: coord[coord.length - 3] })
          newRectangle.text = rowText
        }
        newRectangles.push(newRectangle)
      })
      info[1].forEach((col) => {
        const fieldName = col[4]
        const fieldIndex = fields.findIndex(f => f.field == fieldName)
        fields[fieldIndex].completed = true
        const newRectangle = {
          x: col[0],
          y: col[1],
          width: col[2],
          height: col[3],
          text: fields[fieldIndex]?.text,
          row: false,
          column: true,
          file: col[5],
          imageName: col[6],
          field: fieldName
        }
        newRectangles.push(newRectangle)
      })
      const fieldsState = [...fields, ...newFields]
      let filesState = new Array(info[2]?.length)
      newRectangles.forEach((rect) => {
        const archivo = info[2]?.find(f => f[0] == rect?.imageName)
        if (archivo && rect.row) {
          filesState[rect.file] = archivo
        }
      })
      filesState = filesState.filter(f => f)
      const notOrderedFiles = [...info[2]]
      filesState.forEach(f => {
        const deleteIndex = notOrderedFiles.findIndex(nFile => nFile[0] == f[0])
        if (deleteIndex != -1) {
          notOrderedFiles.splice(deleteIndex, 1)
        }
      })
      filesState = [...filesState, ...notOrderedFiles]
      setFields(fieldsState)
      setRectangles([...newRectangles])
      setFiles(filesState)
      setName(info[3])
      setLoading(false)
    }).catch(setError)
  }, [])

  return (
    <Main className={`grid p-4 ${(loading || training) && "justify-items-center justify-center"}`}>
      {(!error) ? (files.length && name) ? (
        <FormatEditing rectangles={rectangles} name={name} loading={loading} training={training} setTraining={setTraining} setLoading={setLoading} setRectangles={setRectangles} endpoint="update" files={files} setFiles={setFiles} fields={fields} setFields={setFields} />
      ) : (
        <Loader />
      ) : <Error/>}
    </Main>
  )
}

export default EditFormat