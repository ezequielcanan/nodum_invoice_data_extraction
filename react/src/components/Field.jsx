const Field = ({text, field, completed, focused, onClick, children}) => {
  const textColor = focused ? "bg-blue-500 text-white" : (completed ? "bg-green-700 text-white" : "text-white bg-red-600");
  return (
    <div className={`border-current border-2 p-2 rounded-md flex justify-between items-center ${textColor} duration-300 hover:translate-x-2 text-lg cursor-pointer`} onClick={() => onClick(field)}>
      <p>{text}</p>
      {children}
    </div>
  );
};

export default Field;