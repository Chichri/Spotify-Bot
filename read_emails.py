import email 
import imaplib
import yaml
import time
import os

# read credentials for gmail account 
with open("config.yaml") as f_obj:
    content = f_obj.read() 

creds = yaml.load(content, Loader=yaml.FullLoader) # making a yaml object with the proper credentials 
user, pswd = creds["user"], creds["password"] # Extacting the credentials into variables
imap_url = 'imap.gmail.com' # Connecting to gmail with ssl


def filter(body):
    lines = body.split('\n') 
    for line in lines: 
        f = line.find("bump")
        e = line.find(";")
        if f != -1 and e != -1: 
            commandstring = line[f:e]
            t = commandstring.split()
            command = t[1]
            print('command: ' + command)
            return 
            
    print("No valid command found")

def parse(): 
    #TODO write parsing function to interact with spotify api
    return 0



# listen is where the email magic happens. Using the imaplib module, we connect to the account, read new emails, and parse them
def listen(): 
    my_mail = imaplib.IMAP4_SSL(imap_url)
    my_mail.login(user, pswd)
    my_mail.select('Inbox') 
    key = 'FROM'
    value = 'emailgoeshere'
    _, data = my_mail.search(None, key, value)  #Search for emails with specific key and value

    mail_id_list = data[0].split()  #IDs of all emails that we want to fetch 
    print(mail_id_list)

    msgs = [] # empty list to capture all messages
    #Iterate through messages and extract data into the msgs list
    for num in mail_id_list:
        typ, data = my_mail.fetch(num, '(RFC822)') #RFC822 returns whole message (BODY fetches just body)
        msgs.append(data)


    for msg in msgs[::-1]: # Going through the messages in the reverse order (to get most recent ones first I guess?)
        for response_part in msg:
            if type(response_part) is tuple:
                my_msg=email.message_from_bytes((response_part[1]))
                print("_________________________________________")
                print ("subj:", my_msg['subject'])
                print ("from:", my_msg['from'])
                print ("body:")
                for part in my_msg.walk():  
                    if part.get_content_type() == 'text/plain': 
                        filter(part.get_payload())

    # Sets the "to be deleted" flag on all emails that go through, setting up the expunge to later clear out the account, 
    # and filtering emails that have already been read once by removing them from the "inbox" mailbox 

    # for num in mail_id_list: 
        # my_mail.store(num, '+FLAGS', '\\Deleted') 



    my_mail.logout()
    time.sleep(3) 
    os.system('clear')

# while 1:
    # listen() 

                

