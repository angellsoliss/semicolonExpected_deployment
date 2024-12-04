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

#load .env file, get client secret, id
load_dotenv()
client_id = os.getenv("CLIENT_ID")
client_secret = os.getenv("CLIENT_SECRET")

#determine permissions for app
scope = 'user-modify-playback-state user-read-playback-state playlist-modify-public playlist-modify-private playlist-read-private playlist-read-collaborative user-library-read user-top-read'


REDIRECT_URI = "http://localhost:5000/access_token"

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

    #get user information
    global username
    username = sp.current_user()['display_name']
    response = sp.current_user_top_artists(limit=10)
    global top_artists
    top_artists = [artist['name'] for artist in response['items']]
    token = session['access_token']

    #print info, used for debugging
    print(username)
    print(top_artists)
    print(session['access_token'])

    #render html page, pass username and user_email variables so they can be displayed
    return render_template('functionality.html', username=username, top_artists=top_artists, token=token)

#run app
if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
