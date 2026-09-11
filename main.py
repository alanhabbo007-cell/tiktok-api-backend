import requests
from fastapi import FastAPI, HTTPException, Request

app = FastAPI()

def expandir_url(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        respuesta = requests.get(url, allow_redirects=True, headers=headers, timeout=5)
        return respuesta.url
    except:
        return url

@app.get("/obtener_video")
def obtener_video(url: str, request: Request):
    try:
        # 1. Expandimos la URL por si viene acortada
        url_final = expandir_url(url)
        url_limpia = url_final.split("?")[0]

        # 2. Usamos la API especializada (gratuita y sin marca de agua)
        api_url = f"https://www.tikwm.com/api/?url={url_limpia}"
        respuesta_api = requests.get(api_url).json()

        if respuesta_api.get("code") != 0:
            raise Exception("No se pudo obtener la información de TikTok.")

        datos = respuesta_api.get("data", {})
        titulo = datos.get("title", "TikTok_Descarga")
        autor = datos.get("author", {}).get("unique_id", "usuario_desconocido")

        # 3. ¿Es una galería de fotos?
        if "images" in datos and isinstance(datos["images"], list):
            return {
                "estado": "exito",
                "tipo": "fotos",
                "titulo": titulo,
                "uploader": autor,
                "url_descarga": None,
                "urls_fotos": datos["images"] # Ya vienen los enlaces .jpg directos
            }
        
        # 4. Es un video normal
        else:
            # La API nos da el enlace directo al MP4 sin marca de agua
            url_video_directo = datos.get("play")
            
            return {
                "estado": "exito",
                "tipo": "video",
                "titulo": titulo,
                "uploader": autor,
                "url_descarga": url_video_directo,
                "urls_fotos": None
            }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
