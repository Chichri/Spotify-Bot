import yaml
import os

path = os.path.dirname(os.path.abspath(__file__))

with open(path + "/config.yaml") as f_obj:
    content = f_obj.read() 

creds = yaml.load(content, Loader=yaml.FullLoader) # making a yaml object with the proper credentials 
device = creds["device"]

def get_first_available_device(spotify):
    available_devices = spotify.playback_devices()
    #Uncomment this for-loop to print the names of available devices on the account 
    #The device needs to running an active spotify session to show up (a song needs to be playing on it)
    # for av_device in available_devices: 
        # print(av_device.name)

    # if the device field isn't filled out, we default to checking if the first device is active and available
    if device == None:  

        # If we have no available devices, exit the program
        if len(available_devices) == 0:
            print('No devices are available for this user.\nExiting...')
            exit()

        if available_devices[0].is_active:
            return available_devices[0]
        else:
            print(
                f'{available_devices[0].name} ({available_devices[0].type}) is not currently active.\nPlease play and pause a song on it and try again.\nExiting...')
            exit()

    # if the device field is filled out, we default to see if the device with the corresponding name is active.
    else: 

        if len(available_devices) == 0:
            print('No devices available, is ' + device + ' on and running an active spotify session?\nExiting...')
            exit()

        for dev in available_devices:
            
            if dev.name == device: 
                return dev

        print(
            device + ' is not currently active.\nPlease play and pause a song on it and try again.\nExiting...')
        exit()

