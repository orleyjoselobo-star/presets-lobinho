import os
import base64
import requests
from flask import Flask, request
import telebot

# Configuración desde variables de entorno de Google Cloud
TOKEN_TG = os.environ.get('TOKEN_TG')
TOKEN_GH = os.environ.get('TOKEN_GH')
REPO = "orleyjoselobo-star/presets-lobinho"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO}/contents"

# Eliminamos 'threaded=False' para mejorar la compatibilidad con Cloud Run
bot = telebot.TeleBot(TOKEN_TG)
app = Flask(__name__)

@app.route('/' + TOKEN_TG, methods=['POST'])
def getMessage():
    """Maneja las actualizaciones de Telegram enviadas vía Webhook"""
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        # Sincronizamos el procesamiento para evitar cierres prematuros en Cloud Run[cite: 2]
        bot.process_new_updates([update])
        return "OK", 200
    else:
        return "Error de Formato", 403

def upload_to_github(path, content, message):
    """Sube el contenido codificado en Base64 a la API de GitHub[cite: 2]"""
    url = f"{GITHUB_API_URL}/{path}"
    headers = {
        "Authorization": f"token {TOKEN_GH}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Verificamos si el archivo existe para obtener su SHA (necesario para actualizar)[cite: 2]
    res = requests.get(url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    payload = {
        "message": message,
        "content": base64.b64encode(content).decode('utf-8'),
        "branch": "main" # Forzamos la rama principal vista en tu repo[cite: 2]
    }
    
    if sha:
        payload["sha"] = sha
        
    return requests.put(url, json=payload, headers=headers)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """Procesa y sube imágenes JPG a la carpeta 'img/'[cite: 2]"""
    try:
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Usamos el ID de chat y el ID de mensaje para un nombre único[cite: 2]
        name = f"preset_{message.chat.id}_{message.message_id}"
        
        response = upload_to_github(f"img/{name}.jpg", downloaded_file, f"Upload image: {name}")
        
        if response.status_code in [200, 201]:
            bot.reply_to(message, f"📸 Foto guardada en img/{name}.jpg\n\n¡Ahora envía el archivo .dng!")
        else:
            bot.reply_to(message, f"❌ Error al subir a GitHub: {response.status_code}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error interno: {str(e)}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    """Procesa y sube archivos DNG a la carpeta 'presets/'[cite: 2]"""
    try:
        if not message.document.file_name.lower().endswith('.dng'):
            bot.reply_to(message, "⚠️ El archivo debe tener extensión .dng")
            return

        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        name = f"preset_{message.chat.id}_{message.message_id}"
        response = upload_to_github(f"presets/{name}.dng", downloaded_file, f"Upload preset: {name}")
        
        if response.status_code in [200, 201]:
            bot.reply_to(message, f"✅ Archivo {name}.dng guardado con éxito.")
        else:
            bot.reply_to(message, f"❌ Error en GitHub: {response.status_code}")
    except Exception as e:
        bot.reply_to(message, f"⚠️ Error interno: {str(e)}")

if __name__ == "__main__":
    # Configuración de puerto para entorno local y Cloud Run[cite: 2]
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
