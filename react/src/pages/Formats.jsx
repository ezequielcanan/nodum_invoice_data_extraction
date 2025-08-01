import { useEffect, useState } from "react"
import customAxios from "../config/axios.config"
import Loader from "../components/Loader"
import { Link } from "react-router-dom"
import Format from "../components/Format"
import Main from "../containers/Main"
import Error from "../components/Error"

const Formats = () => {
  const [formats, setFormats] = useState([])
  const [error, setError] = useState(false)
  useEffect(() => {
    customAxios.get("/formats").then((res) => setFormats(res.data.payload)).catch(setError)
  }, [])
  return (
    <Main className="py-8 gap-y-[20px] flex flex-col">
      {error ? (
        <Error/>
      ) : (
      !formats ? (
        <Loader />
      ) : (
        <>
          <h1 className="text-3xl font-bold text-white">Formatos</h1>
          <section className={`grid grid-cols-5 gap-8`}>
            {formats.length ? formats.map((format, i) => {
              const isTrained = format[2]
              const borderColor = isTrained ? "border-green-500" : "border-yellow-500"
              return <Format key={i} format={format} borderColor={borderColor} isTrained={isTrained}/>
            }) : (
              <p className="text-lg text-white">No hay formatos creados</p>
            )}
          </section>
        </>))}
    </Main>
  )
}

export default Formats