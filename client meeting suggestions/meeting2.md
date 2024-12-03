- Improve speech recognition speed, there is no feedback from the web page, however the output from the terminal is useful. Less important though, mainly speed. As a user, I don't care what it thinks I'm saying, just that it _knows_ what I'm saying fairly quickly. 1-3 seconds is ideal for a command to be processed. 


- A status text somewhere informing the user that the app is currently listening or not listening


- Start/Stop buttons should clarify what they are doing, should indicate that it is related to the microphone listening mode


- Playlist selection should be more intuitive, if I'm currently listening to a playlist, and I select a new one from the GUI, perhaps have it immediately start playing the first song in that playlist.

-Cache spotify api token to avoid having to login every time the app starts up. Likely need to check the expiry time of a cached token on startup and if it's not expired, then use it. Also look into refreshing the token used over a long period of time. Depends on how long the token lasts, if it's 1 hour, then refreshing should be important, and can you refresh without interactive login?