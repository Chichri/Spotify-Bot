import email 
from email.message import EmailMessage
import imaplib
import smtplib
import ssl
import yaml
import time
import os
import queue
import threading
from bump import bump, get_name
from timer import Timer

path = os.path.dirname(os.path.abspath(__file__))

flush_flag = True
buffer = queue.Queue()
# read credentials for gmail account 
with open(path + "/config.yaml") as f_obj:
    content = f_obj.read() 

userdic = {}
with open(path + '/users.txt') as f_obj:
    useraddrs = f_obj.read().splitlines()
    for useradd in useraddrs: 
        userdic[useradd] = {'track_time': None, 'album_time': None}

# This line makes the timer object used for check cool downs. The last two parameters are the time values
# for tracks and albums/playlists respectively. If you want to change the cooldown times, change these values
# to match your desired time in seconds
track_timeout = 180
album_timeout = 3600
t = Timer(userdic, track_timeout, album_timeout)

creds = yaml.load(content, Loader=yaml.FullLoader) # making a yaml object with the proper credentials 
user, pswd = creds["user"], creds["password"] # Extracting the credentials into variables
imap_url = 'imap.gmail.com' # Connecting to gmail with ssl

# record prints a command out and also writes it to the records.txt file for posterity / debugging purposes
def record(string): 
    print(string)
    with open("records.txt",'a') as f_obj:
        f_obj.write(string + "\n")
        f_obj.close()

# filter is what parses the command type from the content of the command. It returns the command type and the 
# subsequent search string. If it can't find a valid command, then it returns null values instead.
def filter(body):
    lines = body.split('\n') 
    for line in lines: 
        # This line finds specifically a bump and a ; on the same line, returning the parsed command type and
        # search string in the conditional structure below
        f = line.find("bump")
        e = line.find(";")
        if f != -1 and e != -1: 
            command = line[f:(e+1)]
            # Appending a space to the command in case it's a pause or play command, which would fail on the
            # split with no space in the string
            command = command + ' '
            bump, search_string = command.split(' ', 1)
            # every valid command begins with one of these cases
            match bump:
                case "bump":
                    return 'track', search_string
                case "bump:a":
                    return 'album', search_string
                case "bump:p":
                    return 'playlist', search_string
                case "bump:v":
                    return 'volume', search_string
                case "bump:pt":
                    return 'priority-track', search_string
                case "bump:pa":
                    return 'priority-album', search_string
                case "bump:pp":
                    return 'priority-playlist', search_string
                case "bump:pause;":
                    return 'pause', ' '
                case "bump:play;":
                    return 'play', ' ' 
    # If no valid commands were returned in the for loop, return None values
    return None, None

# whitelist checks to see if the sender is a cleared user for the script, while also checking 
# to see which level of user they are. This is done by returning 0 for superusers, 1 for users, and 
# 2 for unrecognized addresses
def whitelist(address):
    with open(path + "/users.txt") as f_obj:
        userlines = f_obj.read().splitlines() 
    with open(path + "/superusers.txt") as f_obj:
        superuserlines = f_obj.read().splitlines()
    if address in superuserlines: 
        return 0
    elif address in userlines: 
        return 1
    else: 
        return 2 

#processCommand parses the scraped command, invoking the bump command with the correct permissions, in the
#correct mode, etc
def processCommand(address, perms, command_type, search_string, t):
    # If command_type is none, filter failed to find a validly formatted command from an authorized user.
    # Thus, we notify the user, we don't start a timer since no song is queue, and we return
    if command_type == None: 
        record(address + " submitted an incorrectly formatted command.")
        reponse_email("Command not accepted", "You didn't submit a properly formatted command. Did you forget the semi-colon?")
        return

    # Now, we handle proper commands. If their a user, we need to determine which timer to look for/start and
    # record it properly
    
    # Firstly we define some strings that get printed out to the terminal / recorded upon the reception of a
    # command. cdown concatenates the search string directly in the invocation of record in case it contains 
    # a %, which would mess with the fstring formatting.

    bump_string = "bumping: " + search_string + ", " + "command type: " + command_type + ", perms: " + str(perms) + ", by :" + address
    cdown_string = address + " is still on a %s cooldown. Search string was: "       
    
    match perms:
        case 1:
            #get timers from t. If a timer isn't none, then it's still on a cool down.
            track_time, album_time = t.return_timers(address)

            if command_type == 'track':
                if track_time != None:
                    record((cdown_string % "track") + search_string)
                    # Calculate the approximate time left in minutes
                    true_time = (track_timeout - (time.perf_counter() - track_time)) // 60
                    if true_time == 0: 
                        time_left = "Less then a minute"
                    else: 
                        time_left = str(int(true_time)) + " minutes"
                    response_email(address, "You're still on a track cooldoown", "Time left: " + time_left)
                    return
                else: 
                    buffer.put((search_string, command_type, perms))
                    record(bump_string)
                    queued_track, artist = get_name(search_string, 't')
                    t.start_track_timer(address)
                    response_email(address, "Command Successfully Submitted!", "Song queued: " + queued_track + ", " + artist)
                    return

            elif (command_type == 'album' or command_type == 'playlist'):
                if album_time != None: 
                    record((cdown_string % "album/playlist") + search_string)
                    # Calculate the approximate time left in minutes
                    true_time = (album_timeout - (time.perf_counter() - album_time)) // 60
                    if true_time == 0: 
                        time_left = "Less then a minute"
                    else: 
                        time_left = str(int(true_time)) + " minutes"
                    response_email(address, "You're still on an album/playlist cooldoown", "Time left: " + time_left)
                    return 
                else:
                    buffer.put((search_string, command_type, perms))
                    record(bump_string)
                    if command_type == 'album':
                        queued_album, artist = get_name(search_string, 'a')
                    else: 
                        queued_album, artist = (search_string, 'you')
                    t.start_album_timer(address)
                    response_email(address, "Command Successfully Submitted!", "Album/playlist queued: " + queued_album + ", " + artist)
                    return
        case 0:
            # And if its a superuser, just queue the command in the buffer with no cooldown checks at all.
            buffer.put((search_string, command_type, perms))
            record(bump_string)
            response_email(address, "Command Successfully Submitted!", "Command Successfully Submitted!")

# listen is where the email magic happens. Using the imaplib module, we connect to the account, read new emails, and parse them
def listen(): 

    t.check_time()

    my_mail = imaplib.IMAP4_SSL(imap_url)
    my_mail.login(user, pswd)
    my_mail.select('Inbox') 
    _, data = my_mail.search(None, 'ALL')  #Get all emails in account
    # _, data = my_mail.search(None, 'FROM', user)  #Get all emails in account

    mail_id_list = data[0].split()  #IDs of all emails that we want to fetch 

    msgs = [] # empty list to capture all messages
    #Iterate through messages and extract data into the msgs list
    for num in mail_id_list:
        typ, data = my_mail.fetch(num, '(RFC822)') #RFC822 returns whole message (BODY fetches just body)
        msgs.append(data)

    for msg in msgs[::-1]: # Going through the messages in the reverse order (to get most recent ones first I guess?)
        for response_part in msg:
            if type(response_part) is tuple:
                my_msg=email.message_from_bytes((response_part[1]))
                line = my_msg['from']
                f = line.find('<')
                e = line.find('>')
                # Scraping the address to compare against the whitelist / permissions level
                address = line[(f+1):e]
                perms = whitelist(address)

                # This conditional stops unrecognized users from submitting commands
                if perms == 2: 
                    record("Unregistered address: " + address + " attempted to submit a command.")
                    continue

                for part in my_msg.walk():  
                    if part.get_content_type() == 'text/plain': 
                        command_type, search_string = filter(part.get_payload())
                        #processCommand does just that. Takes the address, command_type, and search string and
                        #determins the correct way to invoke the bump command
                        processCommand(address, perms, command_type, search_string, t)

    # Sets the "to be deleted" flag on all emails that go through, setting up the expunge to later clear out the account, 
    # and filtering emails that have already been read once by removing them from the "inbox" mailbox 

    for num in mail_id_list: 
        my_mail.store(num, '+FLAGS', '\\Deleted') 

    my_mail.logout()
    time.sleep(3) 

# For manual inputting from the commandline
def manual(): 
    print("Inputting manually... (Enter quit on command type to stop)")

    while True:
        search_string = input("search_string:\n")
        command_type = input("command_type:\n") 
        perms = 0
        if command_type == '': 
            command_type = 'track'
        if command_type == 'a': 
            command_type = 'album'
        if command_type == 'p':
            command_type = 'playlist'
        if command_type == 'v':
            command_type = 'volume'
        if command_type == 'pt': 
            command_type = 'priority-track' 
        if command_type == 'pa': 
            command_type = 'priority-album' 
        if command_type == 'pp': 
            command_type = 'priority-playlist'
        if command_type == 'quit': 
            raise KeyboardInterrupt
        buffer.put((search_string, command_type, perms))


def flush(): 
    global flush_flag
    while True:
        if buffer.empty(): 
            pass
        else: 
            search_string, command_type, perms = buffer.get()
            bump(search_string, command_type, perms)
        time.sleep(1)
        if flush_flag is False: 
            break

def manual_input():
    global flush_flag
    x = threading.Thread(target=flush)
    x.start()
    try:
        manual()
    except KeyboardInterrupt: 
        flush_flag = False 
        x.join()
        flush_flag = True

def read_emails():
    global flush_flag
    x = threading.Thread(target=flush)
    x.start()
    while True:
        try: 
            listen()
        except KeyboardInterrupt: 
            flush_flag = False 
            x.join()
            flush_flag = True
            break

def response_email(address, subject, content):
    context = ssl.create_default_context()
    em = EmailMessage()
    em['From'] = user
    em['To'] = address
    em['Subject'] = subject 
    em.set_content(content)
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(user, pswd)
        smtp.sendmail(user, address,em.as_string())
