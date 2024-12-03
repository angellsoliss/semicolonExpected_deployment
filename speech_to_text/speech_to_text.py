# pip install pyttsx3
# pip install speechrecognition
# pip install pyaudio

import os
import speech_recognition
import pyttsx3 

r = speech_recognition.Recognizer()

def SpeakText(command):
    
    engine = pyttsx3.init()
    engine.say(command)
    engine.runAndWait()

def SpeechToText():
    while(1):
        try:
                with speech_recognition.Microphone() as source2:
                    r.adjust_for_ambient_noise(source2) #adjusts background noise
                    audio2 = r.listen(source2)
            
                MyText = r.recognize_google(audio2) #turn audio into a string
                MyText = MyText.lower() #standardize output as a lowercase string
                return(MyText)
            
        except speech_recognition.RequestError as e:
            print("Could not request results; {0}".format(e))
        
        except speech_recognition.UnknownValueError:
            print("Unintelligible")


###################################################################
#  WakeWordDetect(wakeWord)  #
#Looks for a specific word to be said. 
# If that word is said, listen for the next word and return that
###################################################################
def DetectSpeech(wakeWord):
    possibleWakeWord = SpeechToText()
    if (possibleWakeWord == wakeWord): #If the user said the wake word
        print("Wake Word Detected!")
        print("Listening for command")
        return SpeechToText() #Return the user's command


###Main starts here###

with speech_recognition.Microphone() as source2:
    r.adjust_for_ambient_noise(source2, duration=3) ##Calibrate ambient audio levels
    print("Calibration Complete!")
while(1):
    print("Listening for wake word")
    print(DetectSpeech("program"))
