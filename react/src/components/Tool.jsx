const Tool = ({children, onClick}) => {
  return <button onClick={onClick} className="text-2xl bg-transparent text-white border-current border-2 rounded p-3 duration-300 hover:bg-first hover:text-white active:bg-second">
    {children}
  </button>
}

export default Tool