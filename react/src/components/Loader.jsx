import { Circles, MagnifyingGlass } from "react-loader-spinner"

const Loader = ({glass = false}) => {
  return !glass ? <Circles
  height="80"
  width="80"
  ariaLabel="Cargando"
  wrapperStyle={{}}
  color="#3fa2f6"
  visible={true} /> : <MagnifyingGlass
  height="80"
  width="80"
  ariaLabel="Cargando"
  wrapperStyle={{}}
  color="#3fa2f6"
  visible={true} />
}

export default Loader