import email 
import imaplib
import yaml
import time
import os
import sys
import queue
import threading
from bump import bump

path = os.path.dirname(os.path.abspath(__file__))

flush_flag = True
buffer = queue.Queue()
# read credentials for gmail account 
with open(path + "/config.yaml") as f_obj:
    content = f_obj.read() 

creds = yaml.load(content, Loader=yaml.FullLoader) # making a yaml object with the proper credentials 
user, pswd = creds["user"], creds["password"] # Extacting the credentials into variables
imap_url = 'imap.gmail.com' # Connecting to gmail with ssl

# TODO: make this not a crime against conditional chaining
def filter(body):
    lines = body.split('\n') 
    for line in lines: 
        f = line.find("bump")
        e = line.find(";")
        if f != -1 and e != -1: 
            command = line[f:(e+1)]
            if command == 'bump:pause;':
                return 'pause', ' '
            elif command == 'bump:play;': 
                return 'play', ' ' 
            bump, search_string = command.split(' ', 1)
            if len(bump) == 4: 
                return 'track', search_string
            elif len(bump) == 6: 
                if bump[-1] == 'a': 
                    return 'album', search_string
                elif bump[-1] == 'p': 
                    return 'playlist', search_string
            elif len(bump) == 7: 
                if bump[-1] == 't': 
                    return 'priority-track', search_string
                if bump[-1] == 'a': 
                    return 'priority-album', search_string
                elif bump[-1] == 'p': 
                    return 'priority-playlist', search_string
    # If no vaild commands were returned, return None values
    return None, None

# whitelist checks to see if the sender is a cleared user for the script, while also checking 
# to see which level of user they are. This is done by returning 0 for superusers, 1 for users, and 
# 2 for unrecognized addresses
def whitelist(address):
    with open("users.txt") as f_obj:
        userlines = f_obj.read().splitlines() 
    with open("superusers.txt") as f_obj:
        superuserlines = f_obj.read().splitlines()
    if address in superuserlines: 
        return 0
    elif address in userlines: 
        return 1
    else: 
        return 2 

# listen is where the email magic happens. Using the imaplib module, we connect to the account, read new emails, and parse them
def listen(): 

    my_mail = imaplib.IMAP4_SSL(imap_url)
    my_mail.login(user, pswd)
    my_mail.select('Inbox') 
    # _, data = my_mail.search(None, 'ALL')  #Get all emails in account
    _, data = my_mail.search(None, 'FROM', 'steviemctrash@gmail.com')  #Get all emails in account

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
                    print("Unregistered address: " + address + " attempted to submit a command")
                    continue

                for part in my_msg.walk():  
                    if part.get_content_type() == 'text/plain': 
                        command_type, search_string = filter(part.get_payload())
                        buffer.put((search_string, command_type, perms))
                        print('bumping: ' + search_string + ', ' + 'command type: ' + command_type + ', perms: ' + str(perms) + ', by :' + address)  

    # Sets the "to be deleted" flag on all emails that go through, setting up the expunge to later clear out the account, 
    # and filtering emails that have already been read once by removing them from the "inbox" mailbox 

    for num in mail_id_list: 
        my_mail.store(num, '+FLAGS', '\\Deleted') 

    my_mail.logout()
    time.sleep(3) 

# For manual inputing from the commandline
def manual(): 
    print("Inputting manually... (Enter quit on command type to stop)")

    while True:
        search_string = input("search_string:\n")
        command_type = input("command_type:\n") 
        perms = 0
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


# while 1:
    # listen() 
