import tekore as tk
import time
from auth import get_user_token
from player import get_first_available_device

NUM_ITEMS = 1

# Get the user's token to be able to make requests on their account
token = get_user_token()
spotify = tk.Spotify(token)

# Find the first available device
available_device = get_first_available_device(spotify)

# For shuffling the queue around to play albums in priority.
def prioritize(priority_uri):
    current_volume = spotify.playback().device.volume_percent
    spotify.playback_volume(0) 
    
    currently_playing_uri = spotify.playback_currently_playing().item.uri
    # The sleep call is so that the loop cannot timeout the api with the frequency of requests, which happened a 
    # couple times in testing
    while True:
        spotify.playback_next()
        time.sleep(1) 
        currently_playing_uri = spotify.playback_currently_playing().item.uri
        if currently_playing_uri == priority_uri: 
            spotify.playback_volume(current_volume) 
            break 
        else: 
            spotify.playback_queue_add(currently_playing_uri, device_id=available_device.id)

# get_name returns the title of a song/album and it's artist for the sole purpose of being printed out in the
# response email defined in read_emails. Strictly speaking, bump can do what this function does, but it
# introduces more complexity to get that information across threads. I think this is simpler. 

def get_name(search_string, c):
    match c:
        case 't':
            tracks, = spotify.search(query=search_string, limit=NUM_ITEMS)
            return tracks.items[0].name, tracks.items[0].artists[0].name
        case 'a':
            album, = spotify.search(query=search_string,types=('album',),limit=NUM_ITEMS)
            print(album.items[0].name, album.items[0].artists[0].name)
            return album.items[0].name, album.items[0].artists[0].name

def bump(search_string, command_type, perms): 
    #For queueing a song in the regular fashion
    if command_type == 'track' or command_type == 'priority-track':

        tracks, = spotify.search(query=search_string, limit=NUM_ITEMS)

        if command_type == "priority-track" and perms == 0:
            priority_id = tracks.items[0].id
            spotify.playback_start_tracks([priority_id], device_id=available_device.id) 
            
            # We return early here to avoid queue a song that's already been priority-played
            return 0

        spotify.playback_queue_add(tracks.items[0].uri, device_id=available_device.id)

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
                    #This wont work
                    priority_id = playlist_items.items[0].track.id
                    prioritize(priority_id)

                return 0

        print("Playlist not found: please be exact in the name")
        return 1

    elif command_type == 'pause' and perms == 0: 

        spotify.playback_pause()

    elif command_type == 'play' and perms == 0: 

        spotify.playback_resume()

    elif command_type == 'volume' and perms == 0: 

        try: 
            if int(search_string)< 0 or int(search_string) > 100: 
                print('Volume set must be in range of 0, 100') 
            else: 
                spotify.playback_volume(int(search_string))
        except ValueError: 
            print("Must submit a number for volume")

    else:
        print("Submit a valid command")


## Context About This Code ## 

# Spotify by default makes (at least in my opinion) kind of weird choices when it comes to 
# queueing albums and playlists. When you queue an album and then queue something while the 
# album is playing, the subsequently queued track gets inserted as the next item in the queue
# instead of after all of the items in the album or playlist. I prefer it when these things are 
# treated as continuous items since you tend to listen to them in sequence, so when queueing collections 
# of tracks, instead of actually queueing the album or playlist, it iterates through the tracks 
# and queues them individually and in order so that new tracks get queued in sequence after the 
# collection

## About the two priority functions ## 

# Spotify has an endpoint to just switch the playback to any track, but doing so wipes out the queue. If 
# you have a queue built up, but wanted to play a track immediately without destroying the queue, its 
# actually kind of tricky. There's no endpoint for reordering the queue (even though that is functionality 
# that exists in the gui), so you cannot queue the song you want to play now and then move it forward. 

# I ended up writing two functions to try to implement this functionality. The first solution I came up with was 
# to just queue the song, and then fast-forward through the queue until I reached the desired track. As I skipped 
# a song, I would re-queue it to preserve the queue in the same order until the desired track started playing. The
# same technique was used for priority-queuing albums and playlists. This worked, but resulted in a decent period of
# silence since sleep calls needed to be made during the shuffling to avoid timing out the api. 

# Then I figured out how getting the contents of the queue worked and wrote a tighter function that grabbed the 
# contents of the queue, immediately played the desired track with the queue-destroying endpoint, and then rebuilt
# the queue from its history. However, this function *still* needed sleep calls to not invoke a 503, and it seems to
# stun the application. The queue page in the spotify application become a blank page and trying to queue other stuff 
# through the api gets a 503. This gets cleared up by playing something else like a playlist or something.
# I'll need to test this more to figure it out and see if I can't switch to the faster method

# Until I perfect the second method of re-queueing, I'm keeping the first one as the default uncommented one that gets called 
# when you use the priority command. I'd recommend just manipulating the queue through the application itself if you really
# wanna play things before other things. 

# UPDATE ON THE PRIORITY FUNCTIONS 

# So it appears that endpoint has changed or I was temporarily blind, but either way it no longer seems to
# wipe out the queue when you play a song. I was in the middle of writing a way of locally recording what
# songs were in the queue for a new priority method when I found this. It makes the whole priority thing for
# tracks vastly easier, since the queue is now preserved. For albums, it'll stay as it is. I still keep my old
# counsel of using the gui when re-ordering things.


