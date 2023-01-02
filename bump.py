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

# Spotify by default makes (at least in my opinion) kind of weird choices when it comes to 
# queueing albums and playlists. When you queue an album and then queue something while the 
# album is playing, the subsequently queued track gets inserted as the next item in the queue
# instead of after all of the items in the album or playlist. I prefer it when these things are 
# treated as continuous items since you tend to listen to them in sequence, so when queueing collections 
# of tracks, instead of actually queueing the album or playlist, it iterates through the tracks 
# and queues them individually and in order so that new tracks get queued in sequence after the 
# collection

# This function is my solution to playing things "immediately" in the queue. Spotify has an endpoint 
# to just switch the playback to any track, but doing so wipes out the queue. If you have a queue built up, 
# but wanted to play a track immediately without destroying the queue, its actually kind of tricky. There's 
# no endpoint for reordering the queue (even though that is functionality that exists in the gui) and the 
# endpoint for getting the contents of the queue is essentially non-functional (it usually only returns like
# two of the most upcoming queued songs, and that's only sometimes), which means you cannot easily just grab 
# whats in the queue, start a playback, and then rebuild the queue from what you had. It's certainly doable if 
# you were keeping track of which songs had been queued, but not yet played in the script, but that seemed 
# more unwieldy then what I went with. 

# The solution I came up with was to just queue the song, and then fast-forward through the queue until I reached 
# the desired track. As I skipped a song, I would requeue it to preserve the queue in the same order until the 
# desired track started playing. The same technique is used for priority-queuing albums and playlists
# TODO: Tune up this function to see if it cannot be a bit faster
def prioritize(priority_uri): 
        
        currently_playing_uri = spotify.playback_currently_playing().item.uri
        # The sleep calls are so that the loop cannot "miss" the song with the  frequency of api requests, something
        # that tended to happen when they weren't there
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

def bump(search_string, command_type, perms): 
    #For queueing a song in the regular fashion
    if command_type == 'track' or command_type == 'priority-track':

        tracks, = spotify.search(query=search_string, limit=NUM_ITEMS)
        # print(f' Queueing "{search_string}" on {available_device.name} ({available_device.type})')
        spotify.playback_queue_add(tracks.items[0].uri, device_id=available_device.id)

        if command_type == "priority-track" and perms == 0:
            priority_uri = tracks.items[0].uri 
            prioritize(priority_uri)

        return 0

    #For queueing an entire album
    elif command_type == 'album' or command_type == 'priority-album':

        album, = spotify.search(query=search_string,types=('album',),limit=NUM_ITEMS)
        # print(f'About to queue "{search_string}" on {available_device.name} ({available_device.type})')

        tracks = spotify.album_tracks(album.items[0].id)
        for item in tracks.items: 
            spotify.playback_queue_add(item.uri, device_id=available_device.id)

        if command_type == 'priority-album' and perms == 0:
            priority_uri = tracks.items[0].uri 
            prioritize(priority_uri)


        return 0

    #For queueing a playlist
    elif command_type == 'playlist' or command_type == 'priority-playlist':

        # print(f'About to queue "{search_string}" on {available_device.name} ({available_device.type})')
        user = spotify.current_user()
        #Get list of all playlists and find searched playlist
        playlists = spotify.playlists(user.id) 
        for playlist in playlists.items: 
            if playlist.name == search_string:
                #Get tracks within playlist
                playlist_items = spotify.playlist_items(playlist.id)
                for playlist_track in playlist_items.items: 
                    spotify.playback_queue_add(playlist_track.track.uri)

                if command_type == 'priority-playlist' and perms == 0: 
                    priority_uri = playlist_items.items[0].track.uri
                    prioritize(priority_uri)

                return 0

        print("Playlist not found: please be exact in the name")
        return 1

    elif command_type == 'pause' and perms == 0: 

        # spotify.playback_resume(available_device)
        spotify.playback_pause()

    elif command_type == 'play' and perms == 0: 

        # spotify.playback_resume(available_device)
        spotify.playback_resume()



    else:
        print("Submit a valid command")


