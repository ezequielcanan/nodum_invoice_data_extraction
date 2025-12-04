start "" "react\react.bat"
start "" "backend\server.bat"
cd backend
start "" "mail_listener.bat"
start "" "file_listener.bat"