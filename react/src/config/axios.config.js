import axios from "axios"

const customAxios = axios.create({
  baseURL: `${import.meta.env.VITE_REACT_API_URL}/`,
})

export default customAxios