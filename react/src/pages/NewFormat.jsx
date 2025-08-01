import FirstForm from "../components/FirstForm"
import { useState, useEffect } from "react"
import { useForm } from "react-hook-form"
import * as pdfjsLib from 'pdfjs-dist';
import 'pdfjs-dist/web/pdf_viewer.css';
import FormatEditing from "../components/FormatEditing.jsx";
import { initialFields } from "../utils.js";
import Main from "../containers/Main.jsx";


pdfjsLib.GlobalWorkerOptions.workerSrc = `//cdnjs.cloudflare.com/ajax/libs/pdf.js/${pdfjsLib.version}/pdf.worker.js`;

const NewFormat = () => {
  const [fields, setFields] = useState([...initialFields.map(f => {return {...f}})])
  const [files, setFiles] = useState([])
  const [rectangles, setRectangles] = useState([]);
  const [firstFormSubmitted, setFirstFormSubmitted] = useState(false)
  const [loading, setLoading] = useState(false)
  const [name, setName] = useState(null)
  const [training, setTraining] = useState(false)
  const { register, handleSubmit } = useForm()


  const onSubmitFirstForm = handleSubmit(async data => {
    setName(data?.name)
    setFirstFormSubmitted(true)
  })

  return (
    <Main className={`grid p-4 ${(!firstFormSubmitted || loading || training) && "justify-items-center"}`}>
        {!firstFormSubmitted ? (
          <FirstForm files={files} setFiles={setFiles} register={register} onSubmit={onSubmitFirstForm} />
        ) : (
          <FormatEditing rectangles={rectangles} setFiles={setFiles} name={name} loading={loading} training={training} setTraining={setTraining} setLoading={setLoading} setRectangles={setRectangles} files={files} fields={fields} setFields={setFields} />
        )}
    </Main>
  )
}

export default NewFormat