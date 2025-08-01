import { useEffect, useState } from "react"
import customAxios from "../config/axios.config"
import { useForm } from "react-hook-form"
import { FaLongArrowAltRight } from "react-icons/fa"
import Loader from "../components/Loader"
import Button from "../components/Button"
import Subtitle from "../components/Subtitle.jsx"
import Table from "../components/Table.jsx"
import Main from "../containers/Main.jsx"
import Error from "../components/Error.jsx"

const Test = () => {
  const [formats, setFormats] = useState([])
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(true)
  const [testing, setTesting] = useState(false)
  const [error, setError] = useState(false)
  const [result, setResult] = useState(null)
  const [rows, setRows] = useState([])
  const { handleSubmit, register } = useForm()

  useEffect(() => {
    customAxios.get("/").then((res) => setFormats(res.data.payload), setLoading(false)).catch(setError)
  }, [])

  const onSubmit = handleSubmit(async data => {
    const formData = new FormData()
    formData.append("file", file)
    formData.append("format", data.format)
    setTesting(true)
    const result = await customAxios.post("/test", formData, { headers: { 'Content-Type': 'multipart/form-data', } }).catch(setError)

    result.data.status == "success" ? (setResult(result.data.payload[0]), setRows(result.data.payload[1])) : setError(true)
    setTesting(false)
  })


  return (
    <Main className={`flex py-4 ${!result && "items-center justify-center"} bg-background`}>
      {(loading) ? (<Loader />) : (rows.length && result && !testing) ? (
        <>
          <div className="flex flex-col gap-y-8 ">
            <h1 className="text-3xl text-white font-bold">Datos extraidos de la factura</h1>
            <section className="flex flex-col gap-y-8 text-white">
              <div className="flex flex-col gap-y-2 w-full">
                <Subtitle>Encabezado y pie</Subtitle>
                <Table rows={result} />
              </div>
              <div className="flex flex-col gap-y-2 w-full">
                <Subtitle>Productos / Servicios</Subtitle>
                <Table headers={rows[0]} rows={rows} forRows />
              </div>
            </section>
          </div>
        </>
      ) : (
        !loading
      ) ? (testing ? (
        <div className="flex flex-col gap-y-[30px] items-center justify-center">
          <Loader glass />
          <p className="text-2xl font-bold text-white">Leyendo factura...</p>
        </div>
      ) : formats.length ? (
        <form onSubmit={onSubmit} className="flex flex-col justify-center gap-y-6 p-4 text-2xl">
          <select {...register("format")} className="w-full text-center bg-transparent text-white" defaultValue={formats[0][0] + "," + formats[0][1]}>
            {formats.filter(f => f[2]).map((format, i) => {
              return <option value={format} className="text-black" key={i}>{format[1]}</option>
            })}
          </select>
          <div className="w-full flex items-center">
            <label htmlFor="file" className={`!w-full text-center p-2 text-white ${!file && "border-dashed border-2"}`}>{!file ? "Seleccionar un documento" : `${file.name}`}</label>
            <input type="file" name="file" id="file" className="hidden" onChange={e => setFile(e.target.files[0])} />
          </div>
          <Button type="submit">Testear <FaLongArrowAltRight /> </Button>
        </form>) : !error ? <p className="text-white text-lg">No hay formatos</p> : <Error />
      ) : null}
    </Main>
  )
}

export default Test