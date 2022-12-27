from bump import bump
import queue
import time
import threading

buffer = queue.Queue()

def main(): 

    while True:
        search_string = input("search_string:\n")
        command_type = input("command_type:\n") 
        buffer.put((search_string, command_type))


def flush(): 
    while True:
        if buffer.empty(): 
            pass
        else: 
            search_string, command_type = buffer.get()
            bump(search_string, command_type)
        time.sleep(1)

x = threading.Thread(target=flush)
x.start()
main()
