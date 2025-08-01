const Button = ({children, className, ...props}) => {
  return (
    <button {...props} className={"bg-fifth text-white rounded py-1 flex gap-x-4 items-center justify-center " + className}>{children}</button>
  )
}

export default Button