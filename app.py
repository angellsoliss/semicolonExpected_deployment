import urllib.parse
import json
from flask import Flask, redirect, url_for, render_template, request, jsonify, session
from dotenv import load_dotenv
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
import urllib
import requests
from datetime import datetime
import speech_recognition as sr
import threading

#load .env file, get client secret, id
load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

#determine permissions for app
scope = 'user-modify-playback-state user-read-playback-state playlist-modify-public playlist-modify-private playlist-read-private playlist-read-collaborative user-library-read user-top-read'


REDIRECT_URI = "https://semicolonexpected-deployment.onrender.com/access_token"

#store access token in flask session
cache_handler = FlaskSessionCacheHandler(session)

#initialize speech recognition
r = sr.Recognizer()

#create authentication manager
sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=REDIRECT_URI,
    scope=scope,
    cache_handler=cache_handler,
    show_dialog=True
)

#initialize web app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(64)

#spotify log in page
AUTH_URL = "https://accounts.spotify.com/authorize"

#url to refresh token
TOKEN_URL = "https://accounts.spotify.com/api/token"

global listening
listening = False

def listen_for_commands(access_token):
    global listening

    #create spotipy object, pass access token
    sp = spotipy.Spotify(auth=access_token)

    commands = {
        "next": sp.next_track,
        "previous": sp.previous_track,
        "pause": sp.pause_playback,
        "play": sp.start_playback,
        "mute": lambda: sp.volume(volume_percent=0),
        "volume 25": lambda: sp.volume(volume_percent=25),
        "volume 50": lambda: sp.volume(volume_percent=50),
        "volume 75": lambda: sp.volume(volume_percent=75),
        "volume max": lambda: sp.volume(volume_percent=100),
    }

    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source, duration=0.7)
        
        while True:
            if not listening:
                print("Listening feed stopped")
                #exit if not listening
                return 

            try:
                    #capture speech only if still listening
                    if not listening:
                        print("Stopped before processing audio")
                        return

                    print("Listening for speech...")
                    audio = r.listen(source, timeout=15, phrase_time_limit=20)
                    
                    if not listening:
                        print("stopped before processing recognized speech")
                        return

                    speech = r.recognize_google(audio).lower()
                    print(f"Recognized command: {speech}")

                    #handle commands
                    action = commands.get(speech)
                    if action:
                        action()
                    else:
                        print(f"Unknown command: {speech}")

            except sr.RequestError as e:
                print(f"Could not request results: {e}")
            except sr.UnknownValueError:
                print("Could not understand audio")
            except Exception as ex:
                print(f"Unexpected error: {ex}")

#homepage, what the user sees before they log in with spotify
@app.route('/')
def index():
    return render_template('index.html')

#authenticate user
@app.route('/login', methods=['POST'])
def login():
    params = {
        'client_id' : client_id,
        'response_type' : 'code',
        'scope' : scope,
        'redirect_uri' : REDIRECT_URI,
        'show_dialog' : True
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

#get access token
@app.route('/access_token')
def access_token():
    #check if error occured while logging in
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})

    #if user successfully logs in
    if 'code' in request.args:
        #create request_body to exchange it for access token
        request_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': client_id,
            'client_secret': client_secret
        }

        #send request body to token url to get access token
        response = requests.post(TOKEN_URL, data=request_body)
        token_info = response.json()

        #store acces token and refresh token within session
        session['access_token'] = token_info['access_token']
        session['refresh_token'] = token_info['refresh_token']

        #store token expiration date within token
        session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

        #redirect user to page with their display name and email
        return redirect('/functionality.html')

#get refresh token if current one expires
@app.route('/refresh_token')
def refresh():
    #check if refresh token is in session
    if 'refresh_token' not in session:
        #if refresh token is not in session, prompt user to log in again
        return redirect('/login')
    
    #check if access token has expired
    if datetime.now().timestamp() > session['expires_at']:
        #build request body
        request_body = {
            'grant_type': 'refresh_token',
            'refresh_token': session['refresh_token'],
            'client_id': client_id,
            'client_secret': client_secret
        }

        #request fresh access token using request body
        response = requests.post(TOKEN_URL, data=request_body)
        #store fresh token
        new_token_info = response.json()

        #update session with new token and new expiration time
        session['access_token'] = new_token_info['access_token']
        session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

        #redirect user to page with their display name and email
        return redirect('/functionality.html')

#functionality page, displays username and email
@app.route('/functionality.html', methods=['POST', 'GET'])
def display_name_playlists():
    #if user does not have access token, prompt them to log in
    if 'access_token' not in session:
        return redirect('/login')
    
    #if token has expired, call for refresh token
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh_token')

    #timeout after 10 seconds
    sp = spotipy.Spotify(auth_manager=sp_oauth, auth=session['access_token'], requests_timeout=10)

    #get listening status for display, set to not listening by default by default
    global listening_status
    listening_status = "Not Listening"

    #check listening status, set display to match
    if listening:
        listening_status = "Listening"
    else:
        listening_status = "Not Listening"

    #get user information
    global username
    username = sp.current_user()['display_name']
    response = sp.current_user_top_artists(limit=10)
    global top_artists
    top_artists = [artist['name'] for artist in response['items']]

    #print info, used for debugging
    print(username)
    print(top_artists)

    #render html page, pass username and user_email variables so they can be displayed
    return render_template('functionality.html', username=username, top_artists=top_artists, listening_status=listening_status)

@app.route('/startListening')
def startListening():
    global listening, listening_thread

    if not listening:
        listening = True
        #fetch access token from session
        access_token = session.get('access_token')
        if access_token:
            #start listening thread
            listening_thread = threading.Thread(target=listen_for_commands, args=(access_token,))
            listening_thread.start()
            global listening_status
            listening_status = "Listening"
            print("Listening started")
        else:
            #redirect to login if access token is not found
            return redirect('/login')
    else:
        print("already listening")
    
    return render_template('functionality.html', username=username, top_artists=top_artists, listening_status=listening_status)

@app.route('/stopListening')
def stopListening():
    global listening
    listening = False
    global listening_status
    listening_status = "Not Listening"

    #flush any ongoing operations
    r.energy_threshold = 4000 
    print("Listening stopped by user")
    return render_template('functionality.html', username=username, top_artists=top_artists, listening_status=listening_status)

#run app
if __name__ == '__main__':
    app.run()