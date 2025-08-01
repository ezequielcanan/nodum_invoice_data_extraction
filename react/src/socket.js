import { io } from "socket.io-client"

export const socket = io(`${import.meta.env.VITE_REACT_API_URL}`, {
  reconnection: true,
  reconnectionDelay: 500,
  reconnectionDelayMax: 2000,
  reconnectionAttempts: 99999
})