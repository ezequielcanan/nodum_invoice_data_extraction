import { BrowserRouter, Routes, Route } from "react-router-dom"
import Navbar from "../components/Navbar"
import NewFormat from "../pages/NewFormat"
import EditFormat from "../pages/EditFormat"
import Test from "../pages/Test"
import Formats from "../pages/Formats"
import Home from "../pages/Home"
import Mails from "../pages/Mails"

const Router = () => {
  return (
    <BrowserRouter>
      <Navbar/>
      <Routes>
        <Route path="/" element={<Home/>}/>
        <Route path="/new-format" element={<NewFormat/>}/>
        <Route path="/:id" element={<EditFormat/>}/>
        <Route path="/test" element={<Test/>}/>
        <Route path="/formats" element={<Formats/>}/>
        <Route path="/mails" element={<Mails/>}/>
      </Routes>
    </BrowserRouter>
  )
}

export default Router