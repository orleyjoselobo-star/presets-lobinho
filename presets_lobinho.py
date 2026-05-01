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

# Inicialización del bot (sin threaded para evitar cierres en Cloud Run)
bot = telebot.TeleBot(TOKEN_TG)
app = Flask(__name__)

@app.route('/' + TOKEN_TG, methods=['POST'])
def getMessage():
    """Recibe las actualizaciones de Telegram vía Webhook"""
    # Log básico para confirmar que el mensaje entró al código
    print(f"Update recibido en la ruta del bot") 
    
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    else:
        return "Error de Formato", 403

def upload_to_github(path, content, message):
    """Sube archivos a GitHub usando la API REST[cite: 2]"""
    url = f"{GITHUB_API_URL}/{path}"
    headers = {
        "Authorization": f"token {TOKEN_GH}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Intenta obtener el SHA si el archivo ya existe para actualizarlo[cite: 2]
    res = requests.get(url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    payload = {
        "message": message,
        "content": base64.b64encode(content).decode('utf-8'),
        "branch": "main" # Rama principal del repositorio[cite: 2]
    }
    if sha:
        payload["sha"] = sha
        
    return requests.put(url, json=payload, headers=headers)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """Maneja el envío de imágenes JPG (comprimidas)[cite: 2]"""
    try:
        print("Procesando foto...")
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Nombre único basado en el ID de chat y mensaje[cite: 2]
        name = f"preset_{message.chat.id}_{message.message_id}"
        path = f"img/{name}.jpg"
        
        response = upload_to_github(path, downloaded_file, f"Upload: {name}.jpg")
        
        if response.status_code in [200, 201]:
            bot.reply_to(message, f"📸 Foto guardada en: {path}\n\n¡Ahora envía el archivo .dng!")
        else:
            bot.reply_to(message, f"❌ Error GitHub ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"Error en handle_photo: {e}")
        bot.reply_to(message, "⚠️ Ocurrió un error al procesar la imagen.")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    """Maneja el envío de archivos .dng[cite: 2]"""
    try:
        if not message.document.file_name.lower().endswith('.dng'):
            bot.reply_to(message, "⚠️ Por favor, envía un archivo con extensión .dng")
            return

        print("Procesando archivo DNG...")
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        name = f"preset_{message.chat.id}_{message.message_id}"
        path = f"presets/{name}.dng"
        
        response = upload_to_github(path, downloaded_file, f"Upload: {name}.dng")
        
        if response.status_code in [200, 201]:
            bot.reply_to(message, f"✅ Preset guardado en: {path}")
        else:
            bot.reply_to(message, f"❌ Error GitHub ({response.status_code}): {response.text}")
    except Exception as e:
        print(f"Error en handle_document: {e}")
        bot.reply_to(message, "⚠️ Ocurrió un error al procesar el documento.")

if __name__ == "__main__":
    # Inicio del servidor Flask[cite: 2]
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
