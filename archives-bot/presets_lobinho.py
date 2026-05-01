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

bot = telebot.TeleBot(TOKEN_TG, threaded=False)
app = Flask(__name__)

# Diccionario temporal para emparejar JPG y DNG por usuario
# Esto es útil si envías ambos archivos seguidos
user_data = {}

@app.route('/' + TOKEN_TG, methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

def upload_to_github(path, content, message):
    url = f"{GITHUB_API_URL}/{path}"
    headers = {"Authorization": f"token {TOKEN_GH}"}
    
    # Primero intentamos obtener el SHA si el archivo ya existe
    res = requests.get(url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    payload = {
        "message": message,
        "content": base64.b64encode(content).decode('utf-8')
    }
    if sha:
        payload["sha"] = sha
        
    return requests.put(url, json=payload, headers=headers)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    # Obtener la foto de mayor resolución
    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    # Guardamos temporalmente el nombre sugerido (o usamos el ID)
    name = f"preset_{message.chat.id}"
    upload_to_github(f"img/{name}.jpg", downloaded_file, f"Subida de imagen para {name}")
    bot.reply_to(message, f"📸 Imagen guardada en img/{name}.jpg. ¡Ahora envía el archivo .dng!")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    if not message.document.file_name.lower().endswith('.dng'):
        bot.reply_to(message, "⚠️ Por favor, envía un archivo con extensión .dng")
        return

    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    name = f"preset_{message.chat.id}"
    upload_to_github(f"presets/{name}.dng", downloaded_file, f"Subida de preset {name}")
    
    # AQUÍ PODRÍAMOS AÑADIR LA LÓGICA PARA ACTUALIZAR EL INDEX.HTML AUTOMÁTICAMENTE
    bot.reply_to(message, f"✅ Preset {name}.dng guardado. ¡Repositorio actualizado!")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))