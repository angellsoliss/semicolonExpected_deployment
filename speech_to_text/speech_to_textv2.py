import speech_recognition as sr
import pyttsx3
import threading

#speech recognizer
r = sr.Recognizer()

#initialize tts
tts = pyttsx3.init()

def listen():
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.2)
        audio = r.listen(source, phrase_time_limit=2)
    try:
        #store speech as string
        speech = r.recognize_google(audio).lower()
        print(speech)
    except sr.UnknownValueError:
        print("could not understand the audio")
    except Exception as ex:
        print("Unexpected error:", ex)

def tts_speak(text):
    tts.say(text)
    tts.runAndWait()

#start tts in a separate thread
tts_thread = threading.Thread(target=tts_speak, args=("Listening",))
tts_thread.start()

while True:
    listen()
