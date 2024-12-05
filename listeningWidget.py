import os
import spotipy
import pyttsx3
import speech_recognition as sr
import threading
import tkinter as tk
from tkinter import messagebox
import sys
from tkinter import ttk
import tkinter.font as font

#global listening flag and thread
listening = False
listening_thread = None
r = sr.Recognizer()  #speech recognizer instance
tts = pyttsx3.init()  #text-to-speech engine instance


#redirect statements to mini terminal window on widget
class RedirectText:
    def __init__(self, text_widget):
        self.text_widget = text_widget

    def write(self, text):
        self.text_widget.config(state=tk.NORMAL)  #enable editing temporarily
        self.text_widget.insert(tk.END, text)
        self.text_widget.yview(tk.END)  #scroll to the latest output
        self.text_widget.config(state=tk.DISABLED)  #read only

    def flush(self):
        pass


def listen_for_commands(access_token):
    global listening
    sp = spotipy.Spotify(auth=access_token)

    def save_current_song():
        """Save the currently playing song to the user's liked songs."""
        playback = sp.current_playback()
        if playback and playback.get("item"):
            track_id = playback["item"]["id"]
            track_name = playback["item"]["name"]
            if not sp.current_user_saved_tracks_contains([track_id])[0]:
                sp.current_user_saved_tracks_add([track_id])
                print(f"Saved: {track_name}")
                tts.say(f"Saved {track_name}")
            else:
                print(f"{track_name} is already in your liked songs.")
                tts.say(f"{track_name} is already saved.")
        else:
            print("No song is currently playing.")
            tts.say("No song is currently playing.")
        tts.runAndWait()

    def remove_current_song():
        """Remove the currently playing song from the user's liked songs."""
        playback = sp.current_playback()
        if playback and playback.get("item"):
            track_id = playback["item"]["id"]
            track_name = playback["item"]["name"]
            if sp.current_user_saved_tracks_contains([track_id])[0]:
                sp.current_user_saved_tracks_delete([track_id])
                print(f"Removed: {track_name}")
                tts.say(f"Removed {track_name}")
            else:
                print(f"{track_name} is not in your liked songs.")
                tts.say(f"{track_name} is not saved.")
        else:
            print("No song is currently playing.")
            tts.say("No song is currently playing.")
        tts.runAndWait()

    commands = {
        "next": sp.next_track,
        "previous": sp.previous_track,
        "pause": sp.pause_playback,
        "play": sp.start_playback,
        "repeat": lambda: sp.repeat("track"),
        "continue": lambda: sp.repeat("off"),
        "shuffle": lambda: sp.shuffle(True),
        "order": lambda: sp.shuffle(False),
        "mute": lambda: sp.volume(volume_percent=0),
        "volume 25": lambda: sp.volume(volume_percent=25),
        "volume 50": lambda: sp.volume(volume_percent=50),
        "volume 75": lambda: sp.volume(volume_percent=75),
        "volume max": lambda: sp.volume(volume_percent=100),
        "save": save_current_song,
        "remove": remove_current_song,
    }

    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.7)
        tts.say("Listening")
        tts.runAndWait()

        while listening:
            try:
                print("Listening for speech...")
                audio = r.listen(source, timeout=30, phrase_time_limit=20)
                if not listening:
                    break

                try:
                    speech = r.recognize_google(audio).lower()
                    print(f"Recognized command: {speech}")

                    #handle commands
                    action = commands.get(speech)
                    if action:
                        action()
                    else:
                        print(f"Unknown command: {speech}")
                except sr.UnknownValueError:
                    pass  #ignore and continue
                except sr.RequestError as e:
                    print(f"Could not request results: {e}")

            except Exception as ex:
                print(f"Unexpected error: {ex}")

        print("Exiting listening loop")



#function to start listening for voice commands
def start_listening(access_token):
    global listening, listening_thread

    if not listening:
        listening = True
        listening_thread = threading.Thread(target=listen_for_commands, args=(access_token,))
        listening_thread.start()
        print("Listening started")
    else:
        print("Already listening")


#function to stop listening and join the thread
def stop_listening():
    global listening, listening_thread
    listening = False

    #use a separate thread for gui responsiveness
    def wait_for_thread():
        global listening_thread
        if listening_thread is not None:
            listening_thread.join()
            print("Listening stopped by user")
            listening_thread = None  #reset the thread
        else:
            print("No active listening thread to stop")

    stop_thread = threading.Thread(target=wait_for_thread)
    stop_thread.start()


#tkinter UI
class SpotifyVoiceControlApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Spotify Voice Control")
        self.root.configure(bg="#121212")  # Set dark background
        self.root.geometry("600x475")

        #set font family
        self.default_font = font.Font(family="Poppins", size=12)

        #apply styling to ttk widgets
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TLabel", foreground="white", background="#121212", font=self.default_font)
        style.configure("TButton", foreground="white", background="#1db954", font=self.default_font, padding=5)
        style.map("TButton",
                  background=[("active", "#1ED760")],
                  relief=[("pressed", "sunken"), ("!pressed", "raised")])

        #authorization token input
        self.token_label = tk.Label(root, text="Enter your Spotify authorization token:", bg="#121212", fg="white")
        self.token_label.pack(pady=5)

        self.token_entry = tk.Entry(root, width=50)
        self.token_entry.pack(pady=10)

        #start listening button
        self.start_button = tk.Button(root, text="Start Listening", command=self.start_listening, bg="#1ED760", fg="black")
        self.start_button.pack(pady=10)

        #stop listening button
        self.stop_button = tk.Button(root, text="Stop Listening", command=self.stop_listening, bg="#1ED760", fg="black")
        self.stop_button.pack(pady=10)

        #status label
        self.status_label = tk.Label(root, text="Status: Not Listening", bg="#121212", fg="white")
        self.status_label.pack(pady=10)

        #text widget to display output messages
        self.output_text = tk.Text(root, height=15, width=70, state=tk.DISABLED, bg="#333333", fg="#1db954")
        self.output_text.pack(pady=10)

        #redirect the terminal output to mini terminal in widget
        sys.stdout = RedirectText(self.output_text)

    def start_listening(self):
        #get access token from the entry
        access_token = self.token_entry.get()
        if access_token:
            start_listening(access_token)
            self.status_label.config(text="Status: Listening")
        else:
            messagebox.showerror("Error", "Please enter a valid access token")

    def stop_listening(self):
        stop_listening()
        self.status_label.config(text="Status: Not Listening")


#create the Tkinter root window and run the app
if __name__ == '__main__':
    root = tk.Tk()
    app = SpotifyVoiceControlApp(root)
    root.mainloop()
