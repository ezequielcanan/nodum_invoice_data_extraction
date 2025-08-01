import { useState, useEffect } from "react"
import Subsection from "../containers/Subsection"
import Subtitle from "./Subtitle"
import Coordinate from "./Coordinate"
import Canvas from "./Canvas"
import Field from "./Field"
import { FaChevronLeft, FaChevronRight, FaCross, FaPlus, FaPlusCircle, FaSave, FaTrash, FaTrashAlt } from "react-icons/fa";
import { FaArrowLeftLong, FaArrowRightLong } from "react-icons/fa6";
import { TbMagnet, TbMagnetOff } from "react-icons/tb";
import Tool from "./Tool"
import { socket } from "../socket"
import { useNavigate } from "react-router-dom"
import customAxios from "../config/axios.config"
import Loader from "./Loader"
import Dropdown from "./Dropdown"
import { AnimatePresence, LayoutGroup, motion, Reorder } from "framer-motion"
import { MdClose } from "react-icons/md"

const FormatEditing = ({ rectangles, loading, training, setTraining, setLoading, setRectangles, files, setFiles, fields, name, setFields, endpoint = "upload" }) => {
  const [field, setField] = useState(fields[0] || {})
  const [actualFile, setActualFile] = useState(0)
  const [newRowAdded, setNewRowAdded] = useState(false)
  const [isMagnetActive, setIsMagnetActive] = useState(true)
  const [imageDimensions, setImageDimensions] = useState([])
  const [hasBeenUpdated, setHasBeenUpdated] = useState(false)
  const [loss, setLoss] = useState(100)
  const navigate = useNavigate()

  const prevFile = () => {
    setActualFile(f => f - 1)
  }

  const nextFile = () => {
    setActualFile(f => f + 1)
  }

  function base64ToBlob(base64, mimeType) {
    const byteCharacters = atob(base64);
    const byteNumbers = new Array(byteCharacters.length);
    for (let i = 0; i < byteCharacters.length; i++) {
      byteNumbers[i] = byteCharacters.charCodeAt(i);
    }
    const byteArray = new Uint8Array(byteNumbers);
    return new Blob([byteArray], { type: mimeType });
  }

  const submitData = async (train = true) => {
    setHasBeenUpdated(true)
    const data = new FormData()
    const mimeType = 'application/png'; // Ajusta el tipo MIME según sea necesario
    files.forEach((f,i) => {
      const blob = base64ToBlob(f[1].split(",")[1], mimeType);
      data.append("files", blob, f[0])
    })

    const filasRoi = rectangles.find(r => r.field == "filas")
    const arrayOfCoordinates = rectangles.map((r) => (!r.column) && Object.values({ new: r.new || false, x: r.x, y: r.y, width: r.width, height: r.height, file: r.file, imageName: r.imageName, row: r.row ? 1 : 0, field: r.field })).filter(f => f)
    data.append("fixedCoordinates", arrayOfCoordinates)

    const rows = rectangles.map((r) => r.row && Object.values({ x: (r.x - filasRoi.x), y: (r.y - filasRoi.y), width: r.width, height: r.height, image: r.imageName })).filter(f => f)
    const firstRow = rows[0]
    data.append("rows", rows)
    let lastColumn = []
    const columnsRectangles = rectangles.filter((r) => r.column).sort((a, b) => a.x - b.x)
    const columns = columnsRectangles.map((r) => {
      if (r.column) {
        const column = Object.values({ new: r.new || false, x: passToPercentageX(passToValueX(r.x - firstRow[0]), passToValueX(firstRow[2])), width: Number(r.width), height: Number(r.height), originalx: Number(r.x), originaly: Number(r.y), file: r.file, imageName: r.imageName, field: r.field })
        lastColumn = column
        return column
      }
    }).filter(f => f)
    data.append("columns", columns)
    data.append("name", name)
    data.append("height", imageDimensions[1])
    data.append("width", imageDimensions[0])
    setLoading(true)
    const result = await ((!hasBeenUpdated && endpoint == "upload") ? customAxios.post("/", data, { headers: { 'Content-Type': 'multipart/form-data', } }) : customAxios.put("/", data, { headers: { 'Content-Type': 'multipart/form-data', } }))
    setLoading(false)
    setLoss(100)
    if (train) {
      setTraining(true)
      socket.on('loss', (data) => {
        setLoss(data);
      });
      socket.on("completed", async () => {
        await customAxios.put("/" + result?.data?.id)
        setTraining(false)
        navigate("/test")
      })
      socket.emit("train", name)
    }
  }
  
  const cancelTraining = () => {
    socket.emit("cancel_training")
    setRectangles([...rectangles.map(r => {
      return { ...r, new: false }
    })])
    setLoading(false)
    setTraining(false)
  }

  const saveProgress = () => {
    socket.emit("save")
  }

  const deleteRectangle = (field) => {
    const fieldIndex = getFieldIndex(field)
    fields[fieldIndex].completed = false
    const rectangleIndex = rectangles.findIndex(r => r.field == field)
    if (rectangleIndex != -1) {
      rectangles.splice(rectangleIndex, 1)
    }
    setFields([...fields])
    setRectangles([...rectangles])
  }

  const getFieldIndex = (field) => fields.findIndex((f) => f.field == field)

  const getNextField = (field) => {
    const lastFieldIndex = getFieldIndex(field)
    let nextFieldIndex = (lastFieldIndex + 1)
    nextFieldIndex = nextFieldIndex == fields.length ? 0 : nextFieldIndex
    const nextField = fields.find((f, i) => i == nextFieldIndex)
    fields[lastFieldIndex].focused = false
    fields[nextFieldIndex].focused = true
    setFields([...fields])

    return nextField
  }
  const setFieldCompleted = (fieldName) => {
    const lastField = fields.find(field => field.field == fieldName)
    const lastFieldIndex = fields.findIndex(field => field.field == fieldName)
    lastField.completed = true
    const newFields = [...fields]
    newFields[lastFieldIndex] = lastField
    setFields(newFields)
  }

  const onClickField = (field) => {
    const newFieldsArray = fields.map((f) => {
      return { ...f, focused: false }
    })
    const newFieldIndex = getFieldIndex(field)
    newFieldsArray[newFieldIndex].focused = true
    setFields([...newFieldsArray])
    setField(newFieldsArray[newFieldIndex])
  }


  const addRow = () => {
    const rows = fields.reduce((acc, f) => f.row ? acc + 1 : acc, 0)
    setFields([...fields, { text: `Fila ${rows + 1}`, field: `r${rows + 1}`, completed: false, focused: false, row: true, file: (files[actualFile][0].name || files[actualFile][0]) }])
    setNewRowAdded(rows + 1)
  }


  useEffect(() => {
    if (newRowAdded) {
      const newField = `r${newRowAdded}`;
      if (fields.some(f => f.field === newField)) {
        onClickField(newField);
      }
      setNewRowAdded(false)
    }
  }, [fields, newRowAdded]);

  const isLastFile = actualFile == files.length - 1

  const getFocusedField = () => fields.find((f) => f.focused)?.field

  const getPropertyOfRectangle = (field, property) => rectangles.find(r => r.field == field) ? rectangles.find(r => r.field == field)[property] : ""

  const updateRectangle = (field, property, value) => {
    const rectangle = rectangles.splice(rectangles.findIndex(f => f.field == field), 1)[0]
    rectangle[property] = value
    const newRectangles = [...rectangles, rectangle]
    setRectangles(newRectangles)
  }

  const passToPercentageX = (value, dimension = imageDimensions[0]) => {
    return value * dimension / dimension
  }

  const passToPercentageY = (value, dimension = imageDimensions[1]) => {
    return value * dimension / dimension
  }

  const passToValueX = (value, dimension = imageDimensions[0]) => {
    return Math.round(value / dimension * dimension)
  }

  const passToValueY = (value, dimension = imageDimensions[1]) => {
    return Math.round(value / dimension * dimension)
  }

  const onNewImages = async (e) => {
    const formData = new FormData();
    const selectedFiles = e.target.files
    for (let i = 0; i < selectedFiles.length; i++) {
      formData.append('files', selectedFiles[i]);
    }

    try {
      const response = await customAxios.post('/pdfs', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setFiles([...files, ...response.data]);
    } catch (error) {
      console.error('Error uploading files', error);
    }
  }

  const onDeleteFile = (file, index) => {
    const newRectangles = rectangles.map((rectangle) => {
      if (index == rectangle.file) {
        if (rectangle.row) {
          return undefined
        } else {
          return { ...rectangle, imageName: files[1][0].name || files[1][0] }
        }
      } else if (index < rectangle.file) {
        return { ...rectangle, file: rectangle.file - 1 }
      }
      return rectangle
    })
    const newFields = fields.map((field) => {
      if (field.file == (file[0].name || file[0]) && field.row) {
        return undefined
      }
      return field
    })
    files.splice(index, 1)
    const actualFileAttempt = actualFile == index ? (!index ? 0 : actualFile-1) : actualFile
    setActualFile(files[actualFileAttempt] ? actualFileAttempt : 0)
    setFiles([...files])
    setFields(newFields.filter(f => f))
    setRectangles(newRectangles.filter(r => r))
  }

  const onChangeFileOrder = (newArray) => {
    const imagesIndex = []
    const newImagesIndex = []
    const differences = []
    files.forEach(file => imagesIndex.push(files.indexOf(file)))
    files.forEach(file => newImagesIndex.push(newArray.indexOf(file)))
    imagesIndex.forEach((originalIndex, i) => {
      if (originalIndex != newImagesIndex[i]) {
        differences.push(originalIndex)
      }
    })
    const newRectangles = rectangles.map(rectangle => {
      const rectangleFileIndex = differences.findIndex((d) => d == rectangle.file)
      if (rectangle.row && rectangleFileIndex != -1) {
        return {...rectangle, file: differences[!rectangleFileIndex ? 1 : 0]}
      }
      return rectangle
    })
    setRectangles(newRectangles)
    setFiles(newArray)
  }

  const coordinatesProperties = {
    width: "Ancho",
    x: "X",
    height: "Alto",
    y: "Y"
  }

  const deleteRow = (field) => {
    fields.splice(getFieldIndex(field), 1)
    rectangles.some(r => r.field == field) && rectangles.splice(rectangles.findIndex(r => r.field == field), 1)
    setFields([...fields])
    setRectangles([...rectangles])
  }

  return (
    (!loading && !training) ? (
      <>
        <section className="flex items-center p-4 w-full">
            <Reorder.Group values={files} onReorder={onChangeFileOrder} axis="x" className="grid grid-cols-10 gap-x-8 justify-items-center max-w-full">
              {files.map((file, i) => {
                return <Reorder.Item key={file} value={file} className="relative" onClick={() => setActualFile(i)}>
                  <img src={file[1]} onDragStart={e => e.preventDefault()}/>
                  {files.length > 1 && (<div className="absolute flex flex-col gap-2 top-1 right-1 text-white">
                    <div className="bg-red-500 rounded p-2 cursor-pointer" onClick={(e) =>(e.stopPropagation(), onDeleteFile(file, i))}>
                      <MdClose />
                    </div>
                  </div>)}
                </Reorder.Item>
              })}
              <Reorder.Item className="flex w-full h-full items-center">
                <label htmlFor="file" className={`w-full h-full flex items-center justify-center p-2 border-dashed border-2 cursor-pointer text-white`}><FaPlus /></label>
                <input type="file" name="file" id="file" className="hidden" multiple onChange={onNewImages} />
              </Reorder.Item>
            </Reorder.Group>
        </section>
        <section className="p-4 flex gap-x-[40px] items-start justify-evenly w-full">
          <div className="grid content-start self-start gap-24 sticky top-5">
            <Subsection>
              <Subtitle>Herramientas</Subtitle>
              <div className="grid justify-items-center grid-cols-3 gap-8">
                <Tool onClick={() => submitData(false)}>
                  <FaSave />
                </Tool>
                <Tool onClick={() => setIsMagnetActive(m => !m)}>
                  {isMagnetActive ? <TbMagnet /> : <TbMagnetOff />}
                </Tool>
                <Tool onClick={() => deleteRectangle(field.field)}>
                  <FaTrashAlt />
                </Tool>
              </div>
            </Subsection>
            <Subsection>
              <Subtitle>Coordenadas</Subtitle>
              <div className="grid grid-cols-2 gap-4 w-full">
                {Object.entries(coordinatesProperties).map((p, i) => {
                  return <Coordinate key={i+"coord"} passToPercentage={i > 1 ? passToPercentageY : passToPercentageX} passToValue={i > 1 ? passToValueY : passToValueX} getPropertyOfRectangle={getPropertyOfRectangle} getFocusedField={getFocusedField} updateRectangle={updateRectangle} property={p[0]} text={p[1]} />
                })}
              </div>
            </Subsection>
          </div>
          <Canvas files={files} setImageDimensions={setImageDimensions} imageDimensions={imageDimensions} passToPercentageX={passToPercentageX} passToValueY={passToValueY} passToValueX={passToValueX} passToPercentageY={passToPercentageY} magnet={isMagnetActive} image={files[actualFile][1]} imageName={files[actualFile][0]?.name || files[actualFile][0]} actualFile={actualFile} getNext={getNextField} fields={fields} rectangles={rectangles} setRectangles={setRectangles} setFields={setFields} field={field} setField={setField} setFieldCompleted={setFieldCompleted} />
          <Subsection className="!items-center">
            {!actualFile ? (
              <>
                <Dropdown text={"Encabezado"}>
                  {fields.filter(f => (f.section == "encabezado")).map((f, i) => {
                    return <Field {...f} onClick={onClickField} key={"e" + i} />
                  })}
                </Dropdown>
                <Dropdown text={"Detalle"}>
                  {fields.filter(f => (f.column)).map((f, i) => {
                    return <Field {...f} onClick={onClickField} key={"d" + i} />
                  })}
                </Dropdown>
                <Dropdown text={"Pie"}>
                  {fields.filter(f => (f.section == "pie")).map((f, i) => {
                    return <Field {...f} onClick={onClickField} key={"p" + i} />
                  })}
                </Dropdown>
              </>) : null}

            {fields.some((f) => (f.row) && (f.file == (files[actualFile][0].name || files[actualFile][0]))) ? (
              <Dropdown text={"Filas"}>
                {fields.filter(f => (f.row) && (f.file == (files[actualFile][0].name || files[actualFile][0]))).map((r, i) => {
                  return <Field {...r} onClick={onClickField} key={"row" + r.field}>
                    <FaTrash className="cursor-pointer duration-300 hover:text-red-900" onClick={() => deleteRow(r.field)} />
                  </Field>
                })}
              </Dropdown>
            ) : null}
            <button className={"flex items-center justify-center gap-x-[10px] bg-orange-500 rounded p-2 text-white text-lg"} onClick={addRow}>Agregar Fila <FaPlusCircle /></button>
            <div className={`flex justify-between ${!actualFile && "!justify-end"} gap-x-[20px] text-white`}>
              {actualFile ? <button className={`rounded bg-grey text-xl p-3`} onClick={prevFile}><FaArrowLeftLong /></button> : null}
              {!isLastFile ? <button className={`rounded bg-grey text-xl p-3`} onClick={nextFile}><FaArrowRightLong /></button> : null}
            </div>
            {isLastFile ? (
              <div className="w-full">
                <button className={`rounded bg-blue-500 text-xl p-3 text-white bg-green-700 ${isLastFile && "w-full"}`} onClick={submitData}>Entrenar</button>
              </div>
            ) : null}
          </Subsection>
        </section>
      </>
    ) : (
      <div className="flex flex-col items-center justify-center gap-4">
        <Loader />
        {training ? <>
          <p className="font-semibold text-2xl text-white">Efectividad: %{(100 - loss).toFixed(3)}</p>
          <button className="bg-red-600 p-2 rounded text-2xl text-white font-bold" onClick={cancelTraining}>Cancelar</button>
          {/*<button className="bg-green-600 p-2 rounded text-2xl text-white font-bold" onClick={saveProgress}>Guardar</button>*/}
        </> : null}
      </div>
    )
  )
}

export default FormatEditing