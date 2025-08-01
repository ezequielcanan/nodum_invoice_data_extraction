import { FaLongArrowAltRight } from "react-icons/fa"
import Button from "./Button";
import customAxios from "../config/axios.config";
import { useState } from "react";

const FirstForm = ({ files, setFiles, register, onSubmit }) => {
  const [loadingImages, setLoadingImages] = useState(false)
  const onPdfUpload = async (e) => {
    setLoadingImages(true)
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
      setFiles(response.data);
      setLoadingImages(false)
    } catch (error) {
      console.error('Error uploading files', error);
    }
  }

  return (
    <form onSubmit={onSubmit} className="flex flex-col justify-center gap-y-6 p-4 text-2xl">
      <input type="text" placeholder="Nombre del formato" className="focus:outline-0 text-3xl text-center bg-transparent text-white" {...register("name")} />
      <div className="w-full flex items-center">
        <label htmlFor="file" className={`w-full text-center p-2 border-dashed border-2 cursor-pointer text-white`}>{!loadingImages ? (!files.length ? "Seleccionar documentos" : `${files?.length} archivos subidos`) : "Cargando..."}</label>
        <input type="file" name="file" id="file" className="hidden" onChange={onPdfUpload} multiple />
      </div>
      <Button type="submit" className={`disabled:bg-fifth/70 duration-300`} disabled={loadingImages}>Continuar <FaLongArrowAltRight /> </Button>
    </form>
  )
}

export default FirstForm