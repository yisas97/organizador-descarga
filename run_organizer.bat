
@REM @echo off
@REM :: Cambiar al directorio donde está el .bat
@REM cd /d %~dp0

@REM :: Activar el entorno virtual (usando ruta absoluta)
@REM call "%~dp0venv\Scripts\activate"

@REM :: Ejecutar el script (usando ruta absoluta)
@REM python "%~dp0downloads_organizer.py"

@REM pause

@echo off
cd %~dp0
call venv\Scripts\activate
python downloads_organizer.py