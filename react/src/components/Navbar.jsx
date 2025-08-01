import { FaPlus } from "react-icons/fa"
import { MdMail, MdScience, MdStars } from "react-icons/md"
import { Link, NavLink } from "react-router-dom"

const Navbar = () => {
  return (
    <header className="px-2 py-4 flex flex-col items-center bg-second text-white fixed z-10 gap-y-8 w-[10%] h-screen">
      <Link to={"/"} className="flex items-center justify-center"><img src="logo.png" className="w-4/5 pt-4" alt="" /></Link>
      {/*<h1 className="text-2xl text-center w-full font-bold">Admin Panel</h1>*/}
      <ul className="text-lg flex flex-col gap-y-8">
        <li title="Nuevo formato"><NavLink to={"/new-format"} className={({isActive}) => `flex gap-x-[10px] items-center duration-300 p-2 rounded ${isActive && "text-white bg-first"}`}><FaPlus className="text-xl"/> Nuevo Formato</NavLink></li>
        <li title="Testear modelo de un formato"><NavLink to="/test" className={({isActive}) => `flex gap-x-[10px] items-center duration-300 p-2 rounded ${isActive && "text-white bg-first"}`}><MdScience className="text-xl"/> Test</NavLink></li>
        <li title="Ver formatos de factura"><NavLink to={"/formats"} className={({isActive}) => `flex gap-x-[10px] items-center duration-300 p-2 rounded ${isActive && "text-white bg-first"}`}><MdStars className="text-xl"/> Formatos</NavLink></li>
        <li title="Vincular correos con formatos"><NavLink to={"/mails"} className={({isActive}) => `flex gap-x-[10px] items-center duration-300 p-2 rounded ${isActive && "text-white bg-first"}`}><MdMail className="text-xl"/> Vincular correos</NavLink></li>
      </ul>
    </header>
  )
}

export default Navbar