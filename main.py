import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
import yt_dlp

app = FastAPI()

os.makedirs("descargas", exist_ok=True)
app.mount("/descargas", StaticFiles(directory="descargas"), name="descargas")

@app.get("/obtener_video")
def obtener_video(url: str, request: Request):
    opciones = {
        'quiet': True,
        'outtmpl': 'descargas/%(id)s.mp4', 
        # Buscamos el mejor formato mp4 disponible, si no, el mejor formato general
        'format': 'best[ext=mp4]/best', 
        # Evita que intente descargar cada foto por separado como si fuera un álbum
        'noplaylist': True,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    }
    
    try:
        with yt_dlp.YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Si TikTok lo devuelve como una lista/carrusel, tomamos el elemento principal (el video combinado)
            if 'entries' in info:
                info = info['entries'][0]
            
            titulo = info.get('title', 'Video_TikTok')
            video_id = info.get('id')
            nombre_usuario = info.get('uploader', 'usuario_desconocido')
            
            url_base_segura = str(request.base_url).replace("http://", "https://")
            url_descarga_local = f"{url_base_segura}descargas/{video_id}.mp4"
            
            return {
                "estado": "exito",
                "titulo": titulo,
                "uploader": nombre_usuario,
                "url_descarga": url_descarga_local
            }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
