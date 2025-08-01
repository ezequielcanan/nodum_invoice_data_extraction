import { useEffect, useState } from "react"
import customAxios from "../config/axios.config"
import Main from "../containers/Main"
import Loader from "../components/Loader"
import Button from "../components/Button"
import { CiLink } from "react-icons/ci"
import { useForm } from "react-hook-form"
import Table from "../components/Table"
import Error from "../components/Error"

const Mails = () => {
  const [emails, setEmails] = useState(null)
  const [formats, setFormats] = useState(null)
  const [reload, setReload] = useState(false)
  const [error, setError] = useState(false)
  const {register, handleSubmit, reset} = useForm()

  useEffect(() => {
    customAxios.get("/emails").then((res) => setEmails(res.data.payload)).catch(setError)
    customAxios.get("/").then((res) => setFormats(res.data.payload)).catch(setError)
  }, [reload])

  const onSubmitMail = handleSubmit(async data => {
    await customAxios.post("/emails", JSON.stringify(data), { headers: { 'Content-Type': 'application/json', } }).catch(setError)
    reset()
    setReload(!reload)
  })


  return <Main className={`flex flex-col gap-y-16 py-4 ${!emails && "items-center justify-center"}`}>
    {error ? (
      <Error/>
    ) : (!emails || !formats) ? (
      <Loader/>
    ) : (
      <>
        <div className="flex flex-col gap-y-8">
          <h1 className="text-4xl text-white font-bold">Vincular Correos</h1>
          {formats.length ? <form className="flex gap-8" onSubmit={onSubmitMail}>
            <input type="text" placeholder="Email" {...register("email", {required: {value: true}})} className="text-lg p-2 border-first border-2 text-white bg-transparent focus:outline-none"/>
            <select {...register("formato")} className="text-center bg-transparent text-white text-lg" defaultValue={parseInt(formats[0][0])}>
              {formats.filter(f => f[2]).map((format, i) => {
                return <option value={parseInt(format[0])} className="text-black" key={i}>{format[1]}</option>
              })}
            </select>
            <Button type="submit" className="px-2">Vincular <CiLink className="text-xl"/></Button>
          </form> : <p className="text-lg text-white">No hay formatos</p>}
        </div>
        <Table headers={["Email", "Formato"]} deleteCol rows={emails.map((e) => [e[0], formats.find(f => f[0] == e[1]) ? formats.find(f => f[0] == e[1])[1] : ""])} forTest={false}/>
      </>
    )}
  </Main>
}

export default Mails