import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
import yt_dlp

app = FastAPI()

# Creamos una carpeta temporal en tu PC para guardar los videos
os.makedirs("descargas", exist_ok=True)

# Le decimos a FastAPI que exponga esta carpeta a la red local
app.mount("/descargas", StaticFiles(directory="descargas"), name="descargas")

@app.get("/obtener_video")
def obtener_video(url: str, request: Request):
    opciones = {
        'quiet': True,
        # AHORA SÍ descargamos el video y lo nombramos con su ID
        'outtmpl': 'descargas/%(id)s.mp4', 
        'format': 'mp4', # Aseguramos que sea mp4
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            # download=True fuerza a Python a descargar el video en la PC
            info = ydl.extract_info(url, download=True)
            
            titulo = info.get('title', 'Video_TikTok')
            video_id = info.get('id')

	    # NUEVO: Extraemos el nombre de usuario
            nombre_usuario = info.get('uploader', 'usuario_desconocido')
            
            # request.base_url detecta automáticamente la IP de tu PC (ej. 192.168.0.X:8000)
            # Armamos la ruta local para tu celular
            url_descarga_local = f"{request.base_url}descargas/{video_id}.mp4"
            
            return {
                "estado": "exito",
                "titulo": titulo,
		"uploader": nombre_usuario, # <- Lo agregamos a la respuesta
                "url_descarga": url_descarga_local
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))