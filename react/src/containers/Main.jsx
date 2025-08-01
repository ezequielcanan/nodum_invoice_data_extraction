const Main = ({children, className}) =>  {
  return <main className={"min-h-screen pl-[12%] pr-[2%] bg-background " + className}>{children}</main>
}

export default Main