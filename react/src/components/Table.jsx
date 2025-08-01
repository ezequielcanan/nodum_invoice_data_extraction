import { MdClose } from "react-icons/md"
import { initialFields } from "../utils"

const Table = ({ rows, headers, onDelete,  forRows = false, forTest = true, deleteCol = false }) => {
  return (
    <table className="border-2 border-slate-300">
      <thead className="text-white">
        <tr> 
            {forTest ? (
              <>
                <th className="text-start bg-blue-500 text-xl p-2">{!forRows ? "Campo" : "Fila"}</th>
                {!headers ? (
                  <th className="text-start bg-blue-500 text-xl p-2">Valor</th>
                ) : (
                  Object.keys(headers).map((field) => {
                    return <th className="text-start bg-blue-500 text-xl p-2" key={field}>{initialFields?.find(f => f.field == field)?.text}</th>
                  })
                )}
              </>
            ) : (
              <>
                {headers.map(header => {
                  return <th className="text-start bg-blue-500 text-xl p-2" key={header}>{header}</th>
                })}   
                {/*deleteCol ? (
                  <th className="text-start bg-blue-500 text-xl p-2">Borrar</th>
                ) : null*/}            
              </>
            )}
        </tr>
      </thead>
      <tbody>
        {forTest ? (!forRows ? Object.entries(rows).map((pair, i) => {
          return <tr className={`text-black text-lg ${(i % 2) ? "bg-white" : "bg-slate-200"}`}>
            <td className="p-2">{initialFields?.find(f => f.field == pair[0])?.text}</td>
            <td className="p-2">{pair[1]}</td>
          </tr>
        }) : rows.map((row, i) => {
          return <tr className={`text-black text-lg ${(i % 2) ? "bg-white" : "bg-slate-200"}`}>
            <td className="p-2">{i+1}</td>
            {Object.values(row).map((value, i) => {
              return <td className={`p-2`}>{value}</td>
            })}
          </tr>
        })) : (
          rows.map((row, i) => {
            return <tr className={`text-black text-lg ${(i % 2) ? "bg-white" : "bg-slate-200"}`}>
              {row.map((value, key) => {
                return <td className={`p-2`} key={key+value}>{value}</td>
              })}
              {/*deleteCol ? <td className="p-2"><MdClose/></td> : null*/}
            </tr>
          })
        )}
      </tbody>
    </table>
  )
}

export default Table