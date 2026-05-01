import os
import base64
import requests
from flask import Flask, request
import telebot

# Configuración con tokens fijos para eliminar dudas de variables de entorno
TOKEN_TG = "8611550040:AAHsAR6fqDe8oYM8NfRfph8c5U5hLGxnYV4"
TOKEN_GH = "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"
REPO = "orleyjoselobo-star/presets-lobinho"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO}/contents"

# Inicialización del bot
bot = telebot.TeleBot(TOKEN_TG)
app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def getMessage():
    """Punto de entrada para Telegram"""
    print("--- NUEVA PETICIÓN RECIBIDA EN /WEBHOOK ---")
    try:
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        
        # Log para identificar qué llega al bot
        if update.message:
            if update.message.photo:
                print(f"Contenido detectado: FOTO de {update.message.chat.id}")
            elif update.message.document:
                print(f"Contenido detectado: DOCUMENTO ({update.message.document.file_name})")
            else:
                print("Contenido detectado: OTRO (Texto o comando)")
        
        bot.process_new_updates([update])
        return "OK", 200
    except Exception as e:
        print(f"ERROR CRÍTICO en la recepción: {e}")
        return "Error", 500

def upload_to_github(path, content, commit_message):
    """Función para subir archivos a tu repositorio"""
    url = f"{GITHUB_API_URL}/{path}"
    headers = {
        "Authorization": f"token {TOKEN_GH}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    # Verificamos si el archivo ya existe para obtener su SHA
    res = requests.get(url, headers=headers)
    sha = res.json().get('sha') if res.status_code == 200 else None
    
    payload = {
        "message": commit_message,
        "content": base64.b64encode(content).decode('utf-8'),
        "branch": "main"
    }
    if sha:
        payload["sha"] = sha
        
    print(f"Intentando subir a GitHub: {path}...")
    return requests.put(url, json=payload, headers=headers)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    """Maneja las fotos enviadas como imagen comprimida"""
    try:
        print("Iniciando proceso de descarga de FOTO...")
        file_id = message.photo[-1].file_id
        file_info = bot.get_file(file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        name = f"preset_{message.chat.id}_{message.message_id}"
        path = f"img/{name}.jpg"
        
        response = upload_to_github(path, downloaded_file, f"Upload: {name}.jpg")
        
        if response.status_code in [200, 201]:
            print("ÉXITO: Foto subida a GitHub")
            bot.reply_to(message, f"📸 Foto guardada en img/{name}.jpg\n\n¡Envíame ahora el .dng!")
        else:
            print(f"FALLO GitHub: {response.status_code} - {response.text}")
            bot.reply_to(message, f"❌ Error en GitHub: {response.status_code}")
    except Exception as e:
        print(f"Error en handle_photo: {e}")

@bot.message_handler(content_types=['document'])
def handle_document(message):
    """Maneja los archivos con extensión .dng"""
    try:
        if not message.document.file_name.lower().endswith('.dng'):
            print(f"Archivo rechazado: {message.document.file_name}")
            bot.reply_to(message, "⚠️ El archivo debe ser extensión .dng")
            return

        print("Iniciando proceso de descarga de DNG...")
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        name = f"preset_{message.chat.id}_{message.message_id}"
        path = f"presets/{name}.dng"
        
        response = upload_to_github(path, downloaded_file, f"Upload: {name}.dng")
        
        if response.status_code in [200, 201]:
            print("ÉXITO: DNG subido a GitHub")
            bot.reply_to(message, f"✅ Preset guardado en presets/{name}.dng")
        else:
            print(f"FALLO GitHub: {response.status_code} - {response.text}")
            bot.reply_to(message, f"❌ Error en GitHub: {response.status_code}")
    except Exception as e:
        print(f"Error en handle_document: {e}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
