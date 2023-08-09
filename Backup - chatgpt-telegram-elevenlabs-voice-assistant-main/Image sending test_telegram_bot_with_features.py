
from telegram.ext import Updater, MessageHandler, Filters
import telegram
import openai
from moviepy.editor import AudioFileClip
from elevenlabslib import *
from sklearn.metrics.pairwise import cosine_similarity
from flask import send_file
import io
from telegram import Update
from telegram.ext import CallbackContext
import numpy as np
from PIL import Image
import os
from telegram.ext import CommandHandler


def send_image(update: Update, context: CallbackContext):
    user_request = update.message.text  # This is how you get the text the user sent

    # Assuming 'images' is a dictionary where keys are filenames and values are PIL Image objects
    filename = match_request_to_image(user_request)
    image = images.get(filename)
    

    if image:
        # Convert the PIL Image object to a byte stream
        byte_stream = io.BytesIO()
        image.save(byte_stream, format='PNG')
        byte_stream.seek(0)

        # Send the image
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=byte_stream)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I couldn't find the image you're looking for.")

def match_request_to_image(user_request):
    # This is a placeholder function that simply returns the user request appended with '.jpg'
    # Replace this with your actual logic for matching requests to image filenames
    return user_request + '.png'



openai.api_key = "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"
TELEGRAM_API_TOKEN = "6586471421:AAE0ihQwGGyQAANkU6jji9QBy1ysqJs_8SY"
ELEVENLABS_API_KEY = "9ebc5a24de61ec4d94c8510abead6d82"

user = ElevenLabsUser(ELEVENLABS_API_KEY)
voice = user.get_voices_by_name("Angelina")[0]

image_folder = 'images'

image_files = [os.path.join(image_folder, filename) 
               for filename in os.listdir(image_folder) 
               if not filename.startswith('.') and filename.endswith('.png')]

# Try to open each image file and store it in a dictionary
# If an error occurs when opening a file, it will be skipped
images = {}
for image_file in image_files:
    try:
        filename = os.path.basename(image_file)
        images[filename] = Image.open(image_file)
    except Exception as e:
        print(f"Could not open {image_file}: {e}")

# Here you would load the text file into memory
# You might need to adjust this part based on how you want to use the text file
with open('persona.txt', 'r') as file:
    persona = file.read()

# Initialize the memory
memory = []


messages = messages = [
    {"role": "system", "content": persona},
    {"role": "system", "content": "You are as a role of my bestfriend, now lets play the following requirements: 1/ your name is Angelina Jolie you are sarcastic. Lastly Use this conversation history to make your decision."}
]


def text_message(update, context):
    ...
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=memory + messages
    )
    ...
    update.message.reply_text(
        "...")
    messages.append({"role": "user", "content": update.message.text})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    response_text = response["choices"][0]["message"]["content"]
    messages.append({"role": "assistant", "content": response_text})
    response_byte_audio = voice.generate_audio_bytes(response_text)
    with open('response_elevenlabs.mp3', 'wb') as f:
        f.write(response_byte_audio)
    context.bot.send_voice(chat_id=update.message.chat.id,
                           voice=open('response_elevenlabs.mp3', 'rb'))
    
    context.bot.send_message(chat_id=update.effective_chat.id, text=response["choices"][0]["message"]["content"].strip())
    # Add the user's message to memory
    memory.append({"role": "user", "content": update.message.text})

def handle_message(update: telegram.Update, context: telegram.ext.CallbackContext) -> None:
    user_request = update.message.text
    # Decide which image to send based on the user's request
    image_filename = match_request_to_image(user_request)  # You need to define this function
    image = images[image_filename]
    # Send the image
    chat_id = update.message.chat_id
    context.bot.send_photo(chat_id, photo=open(image.filename, 'rb'))
    


def voice_message(update, context):
    ...
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=memory + messages
    )
    ...
    update.message.reply_text(
        "...")
    voice_file = context.bot.getFile(update.message.voice.file_id)
    voice_file.download("voice_message.ogg")
    audio_clip = AudioFileClip("voice_message.ogg")
    audio_clip.write_audiofile("voice_message.mp3")
    audio_file = open("voice_message.mp3", "rb")
    transcript = openai.Audio.transcribe("whisper-1", audio_file).text
    
    messages.append({"role": "user", "content": transcript})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    response_text = response["choices"][0]["message"]["content"]
    response_byte_audio = voice.generate_audio_bytes(response_text)
    with open('response_elevenlabs.mp3', 'wb') as f:
        f.write(response_byte_audio)
    context.bot.send_voice(chat_id=update.message.chat.id,
                           voice=open('response_elevenlabs.mp3', 'rb'))
    
    messages.append({"role": "assistant", "content": response_text})
    memory.append({"role": "user", "content": update.message.voice})

    # The rest of your code here

updater = Updater(TELEGRAM_API_TOKEN, use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(MessageHandler(
    Filters.text & (~Filters.command), text_message))
dispatcher.add_handler(MessageHandler(Filters.voice, voice_message))
updater.start_polling()
updater.idle()
