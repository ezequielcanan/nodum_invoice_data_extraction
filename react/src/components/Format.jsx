import { Link } from "react-router-dom"

const Format = ({key, format, borderColor, isTrained}) => {
  return <Link key={key} to={"/" + format[0]} className={`bg-second text-white rounded p-4 flex flex-col border-b-8 ${borderColor}`}>
    <div className="flex w-full justify-between items-center">
      <h3 className="text-2xl font-bold">{format[1]}</h3>
      <p className="text-xl">{isTrained ? "Entrenado" : "Guardado"}</p>
    </div>
  </Link>
}

export default Format