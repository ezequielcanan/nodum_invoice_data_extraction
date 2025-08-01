const Coordinate = ({ getPropertyOfRectangle, getFocusedField, updateRectangle, property, text, passToValue, passToPercentage }) => {
  const focusedField = getFocusedField()
  const value = passToValue(getPropertyOfRectangle(focusedField, property))
  return <div className="flex flex-col items-center text-white gap-y-[10px] p-2 rounded border-2 border-white">
    <h3 className="text-lg font-bold">{text}</h3>
    <input type="number" className="max-w-full text-md text-center bg-white/20 focus:outline-none" onChange={(e) => updateRectangle(focusedField, property, passToPercentage(Number(e.target.value)))} value={value} disabled={!value} />
  </div>
}

export default Coordinate