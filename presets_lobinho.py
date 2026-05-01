import os
import base64
import requests
from flask import Flask, request
import telebot

# Tokens insertados textualmente para asegurar la conexión
TOKEN_TG = "8611550040:AAHsAR6fqDe8oYM8NfRfph8c5U5hLGxnYV4"
TOKEN_GH = "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"

REPO = "orleyjoselobo-star/presets-lobinho"
GITHUB_API_URL = f"https://api.github.com/repos/{REPO}/contents"

# Inicialización del bot
bot = telebot.TeleBot(TOKEN_TG)
app = Flask(__name__)

@app.route('/' + TOKEN_TG, methods=['POST'])
def getMessage():
    """Recibe las actualizaciones de Telegram"""
    print("Mensaie recibido desde Telegram con tokens fijos")
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Error", 403
