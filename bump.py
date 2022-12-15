import tekore as tk
import time
from auth import get_user_token
from player import get_first_available_device

NUM_ITEMS = 1

# Get the user's token to be able to make requests on their account
token = get_user_token()
spotify = tk.Spotify(token)

#  Find the first available device
available_device = get_first_available_device(spotify)

def bump(search_string, command_type): 
    #For queueing a song with priority: Whatever's playing currently is skipped and the priority song gets played 
    if command_type == 'priority':

        tracks, = spotify.search(query=search_string, limit=NUM_ITEMS)

        print(f'About to play "{search_string}" on {available_device.name} ({available_device.type})')
        for index, track in enumerate(tracks.items):
            print(index+1, track.name, 'by', track.artists[0].name)

        spotify.playback_queue_add(tracks.items[0].uri, device_id=available_device.id)
        priority_uri = tracks.items[0].uri 
        currently_playing_uri = spotify.playback_currently_playing().item.uri
        #This loop fastforwards through the queue to the song with priority, requeuing the skipped 
        #songs behind it 
        #The sleep calls are so that the loop cannot "miss" the song with the 
        #frequency of api requests, something that tended to happen when they weren't 
        #there
        while True:
            time.sleep(.5) 
            spotify.playback_next()
            time.sleep(.5) 
            currently_playing_uri = spotify.playback_currently_playing().item.uri
            time.sleep(.5) 
            if currently_playing_uri == priority_uri: 
                break 
            else: 
                time.sleep(.5) 
                spotify.playback_queue_add(currently_playing_uri, device_id=available_device.id)

        return 0

    #For queueing a song in the regular fashion
    elif command_type == 'track':

        tracks, = spotify.search(query=search_string, limit=NUM_ITEMS)
        print(f' Queueing "{search_string}" on {available_device.name} ({available_device.type})')
        spotify.playback_queue_add(tracks.items[0].uri, device_id=available_device.id)

        return 0

    #For queueing an entire album
    elif command_type == 'album':

        album, = spotify.search(query=search_string,types=('album',),limit=NUM_ITEMS)
        print(f'About to queue "{search_string}" on {available_device.name} ({available_device.type})')

        tracks = spotify.album_tracks(album.items[0].id)
        for item in tracks.items: 
            spotify.playback_queue_add(item.uri, device_id=available_device.id)

        return 0

    else:
        print("Sumbit a valid command")


