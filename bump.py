import tekore as tk
from auth import get_user_token
from player import get_first_available_device

NUM_ITEMS = 1

# Get the user's token to be able to make requests on their account
token = get_user_token()
spotify = tk.Spotify(token)

#  Find the first available device
available_device = get_first_available_device(spotify)

def bump(search_string, command_type): 
    if command_type == 'priority':

        tracks, = spotify.search(query=search_string, limit=NUM_ITEMS)

        # play the songs!
        print(f'About to play "{search_string}" on {available_device.name} ({available_device.type})')
        for index, track in enumerate(tracks.items):
            print(index+1, track.name, 'by', track.artists[0].name)
        # for playing 

        spotify.playback_queue_add(tracks.items[0].uri, device_id=available_device.id)
        spotify.playback_next() 

        return 0, None


    elif command_type == 'track':

        tracks, = spotify.search(query=search_string, limit=NUM_ITEMS)

        # play the songs!
        print(f' Queueing "{search_string}" on {available_device.name} ({available_device.type})')

        spotify.playback_queue_add(tracks.items[0].uri, device_id=available_device.id)

        return 0, None

    elif command_type == 'album':

        album, = spotify.search(query=search_string,types=('album',),limit=NUM_ITEMS)

        # play the album! 
        print(f'About to queue "{search_string}" on {available_device.name} ({available_device.type})')
        # spotify.playback_start_context(album.items[0].uri, device_id=available_device.id)


        tracks = spotify.album_tracks(album.items[0].id)
        for item in tracks.items: 
            spotify.playback_queue_add(item.uri, device_id=available_device.id)

        last_track_id = tracks.items[-1].id

        return last_track_id, item.uri 

    else:
        print("Sumbit a valid command")



