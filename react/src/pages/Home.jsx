import ParticlesBackground from "../components/ParticlesBackground"

const Home = () => {
  return (
    <main className={`min-h-screen pl-[12%] flex items-center justify-center`}>
      <ParticlesBackground />
      <div className="w-full h-full flex flex-col gap-y-[10px] items-center justify-center relative z-20">
        <img src="logo.png" alt="" className="w-[30%]"/>
        <h1 className="font-bold text-white text-2xl">Lector de Facturas</h1>
      </div>
    </main>
  )
}

export default Home