import time
import os

path = os.path.dirname(os.path.abspath(__file__))

# The Timer class keeps track when users have queued thing and when they can do it again

# In use, Timer is fed a dictionary consisting of every user as the keys, and sub-dictionaries recording
# 'track_time' and 'album_time' as the values. The default values of these sub-dictionary values are None, 
# which represents the base state: a user can queue something. Once something is queued, the appropriate "timer" is 
# started by recording the current uptime of the machine. The program will then periodically check the recorded uptime 
# against the current uptime under the desired difference is reached, indicating that the 'cooldown' period has passed. 
# The appropriate value is then set to None again and user is once more capable of queue things. 

# Playlists and albums use the same "timer", because at least to my mind, they're usually the same length. 

class Timer(): 
    def __init__(self, users, track_time, album_time):
        self.users = users
        self.track_time = track_time
        self.album_time = album_time

    def return_timers(self, user): 
        return self.users[user]['track_time'], self.users[user]['album_time']

    def start_track_timer(self, user): 
        self.users[user]['track_time'] = time.perf_counter()

    def start_album_timer(self, user): 
        self.users[user]['album_time'] = time.perf_counter()

    def check_time(self): 

        for user in self.users: 

            if self.users[user]['track_time'] != None: 
                if (time.perf_counter() - self.users[user]['track_time']) < self.track_time: 
                    pass
                else: 
                    self.users[user]['track_time'] = None

            if self.users[user]['album_time'] != None: 

                if (time.perf_counter() - self.users[user]['album_time']) < self.album_time: 
                    pass
                else: 
                    self.users[user]['album_time'] = None

