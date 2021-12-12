from platform import platform
import socket
import sys
from sys import platform
import os
import time
import string
import random
from os import walk
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler

try:
    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])
    my_folder = sys.argv[3]
    update_time = sys.argv[4]
except:
    sys.exit()
#update_list = []

#server_ip = "127.0.0.1"
#server_port = 33333
#my_folder = "/media/avi/4AF2D834F2D825CB/cloud5"
#update_time = 5

# checking if port is valid. 
if (len(str(server_port)) != 5 or int(server_port) > 65535 or int(server_port) < 0):
    exit()

# checking if IP is valid. 
if (server_ip.count('.') != 3):
    exit()
part = server_ip.split('.')
for i in part:
    if (int(i) > 255 or int(i) < 0):
        exit()



id_number = "0"
pc_id = (''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(50))) # random pc id. 
observer_flag = 0
modified_flag = 0
base = len(my_folder)

# global and temp files dict and dir list. 
files_dict = {}
dir_list = []

try: 
    id_number = sys.argv[5]

except:
    id_number = "0"


if not os.path.exists(my_folder):
        os.makedirs(my_folder)

"""
Input data in bytes, and deserialize the data into dict according protocol:
1) data length
    1.1) name length (4 bytes - int)
    1.2) name
    1.3) content length (4 bytes - int)
    1.4) content
"""
def deserializeDict(data):
    new_dict = {}
    start = 0
    end = 4
    data_len = len(data)
    while(end <= data_len):
        len_name = int.from_bytes(data[start:end], "little")
        name = data[end:end+len_name]
        len_content = int.from_bytes(data[end+len_name:end+len_name + 4], "little")
        content = data[end+len_name + 4:end + len_name + 4 + len_content]
        new_dict[name.decode()] = content
        start = end + len_name + 4 + len_content
        end = end + len_name + 4 + len_content + 4
    return new_dict

"""
Input dictionary, and serealize the dictionary into bytes according protocol:
1) data length
    1.1) name length (4 bytes - int)
    1.2) name
    1.3) content length (4 bytes - int)
    1.4) content
"""

def serializeDict(file_dict):
    data = b''
    for key in file_dict:
        data = data + len(key.encode()).to_bytes(4, "little")
        data = data + key.encode()
        data = data + len(file_dict[key]).to_bytes(4, "little")
        data = data + file_dict[key]
    return data

"""
Input data in bytes, and deserialize the data into list according protocol:
1) data length
    1.1) name length (4 bytes - int)
    1.2) name
"""

def deserializeList(data):
    new_List = []
    start = 0
    end = 4
    data_len = len(data)
    while(end <= data_len):
        len_name = int.from_bytes(data[start:end], "little")
        name = data[end:end+len_name]
        new_List.append(name.decode())
        start = end + len_name
        end = end + len_name + 4
    return new_List

"""
Input list, and serealize the list into bytes according protocol:
1) data length
    1.1) len name (4 bytes - int)
    1.2) name
"""

def serializeList(file_dict):
    data = b''
    for key in file_dict:
        data = data + len(key.encode()).to_bytes(4, "little")
        data = data + key.encode()
    return data


"""
function used for creating file or directory.
protocol:
1) create type, d - for directory, f - for file (1 byte)
2) name length (4 bytes)
3) name
4) content length (just if file)
5) content (just if file.)
"""

def clientCreate(s):
    global observer_flag
    c_type = s.recv(1).decode()
    length = int.from_bytes(s.recv(4),"little")
    if (c_type == 'd'):
        create_path = s.recv(length).decode()
        if not os.path.exists(my_folder + create_path):
            os.makedirs(my_folder + create_path)
    if (c_type == 'f'):
        observer_flag = 1
        f_name = (s.recv(length)).decode()
        f_name = normPath(f_name)
        length_content = int.from_bytes(s.recv(4),"little")
        f_content = recvHelp(s,length_content)
        observer_flag = 0
        my_file = open(my_folder + f_name, 'wb')
        my_file.write(f_content)
        my_file.close()

"""
function used for deleting file or directory.
protocol:
1) create type, d - for directory, f - for file (1 byte)
2) name length (4 bytes)
3) name (path to delete)
"""

def clientDelete(s):
    c_type = s.recv(1).decode()  # line was neccery for the type. (not used because watchdog mistake on windows)
    length = int.from_bytes(s.recv(4),"little")
    delete_path = s.recv(length).decode()
    delete_path = normPath(delete_path)
    if (os.path.isdir(my_folder + delete_path)):
        if os.path.exists(my_folder + delete_path):
            removeFolder(my_folder + delete_path)
            os.rmdir(my_folder + delete_path)
    else:
        if os.path.exists (my_folder + delete_path):
            os.remove(my_folder + delete_path)


def clientModified(s):
    return

"""
function used for moving file or directory.
protocol:
1) length of source path (4 bytes)
2) source path
3) length of destination path (4 bytes)
4) destination path
"""

def clientMove(s):
    length_src = int.from_bytes(s.recv(4),"little")
    src = s.recv(length_src).decode()
    src = normPath(src)
    length_dest = int.from_bytes(s.recv(4),"little")
    desti = s.recv(length_dest).decode()
    desti = normPath(desti)
    if(os.path.exists(my_folder + src)):
        os.replace(my_folder + src, my_folder + desti)


def readSizeHelp(path):
    time.sleep(0.02)
    content_size = os.path.getsize(path)
    if (content_size > 1000000):
        time.sleep(0.2)
        content_size = os.path.getsize(path)
    if (content_size > 20000000):
        time.sleep(5)
        content_size = os.path.getsize(path)
    if(content_size > 400000000):
        time.sleep(6)
        content_size = os.path.getsize(path)
    return content_size



"""
Sending file or derectory creating update.
protocol:
1) "c" for client command in the server protocol.
2) id number of the client.
3) pc id of the computer.
4) "c" for create command. 
5) "d" or "f" for derectory or file. 
5) length of path to create (4 bytes)
6) path to create
7) len of file content (if file)
8) file content.
"""

def sendCreateUpdate(s,update_path, is_dir):
    if(is_dir):
        path_to_send = str(update_path)[base:]
        lengh = len(path_to_send.encode())
        messege = "c".encode() + id_number.encode() + pc_id.encode() + "c".encode() + "d".encode() + lengh.to_bytes(4, "little") + (path_to_send).encode()
        s.send(messege)
    else:
        file_pn = str(update_path)[base:]
        content_size = readSizeHelp(update_path)
        my_file = open(update_path , 'rb')
        file_cn = my_file.read()
        file_byte = len(file_pn.encode()).to_bytes(4, "little") + file_pn.encode() + content_size.to_bytes(4, "little")
        messege = "c".encode() + id_number.encode() + pc_id.encode() + "c".encode() + "f".encode() + file_byte
        s.send(messege)
        s.send(file_cn)
        my_file.close()

"""
Sending file or derectory delete update.
protocol:
1) "c" for client command in the server protocol.
2) id number of the client.
3) pc id of the computer.
4) "d" for create command. 
5) "d" or "f" for derectory or file. 
6) length of source path (4 bytes)
7) source path
8) length of destination path (if file)
9) destination path.
"""

def sendDeleteUpdate(s, update_path, is_dir):
    if(is_dir):
        dir_path = str(update_path)[base:]
        messege = "c".encode() + id_number.encode() + pc_id.encode() + "d".encode() + "d".encode() + len(dir_path.encode()).to_bytes(4, "little") + dir_path.encode()
        s.send(messege)
    else:
        file_path = str(update_path)[base:]
        messege = "c".encode() + id_number.encode()+ pc_id.encode() + "d".encode() + "f".encode() + len(file_path.encode()).to_bytes(4, "little") + file_path.encode()
        s.send(messege)

"""
Sending file or derectory delete update.
protocol:
1) "c" for client command in the server protocol.
2) id number of the client.
3) pc id of the computer.
4) "r" for move command. 
5) length of source path (4 bytes)
6) source path
7) length of destination path (if file)
8) destination path.
"""

def sendMoveUpdate(s, source_path, desti_path):
    source = str(source_path)[base:]
    desti = str(desti_path)[base:]
    source_desti_byte = len(source.encode()).to_bytes(4, "little") + source.encode() + len(desti.encode()).to_bytes(4, "little") + desti.encode()
    messege = "c".encode() + id_number.encode()+ pc_id.encode() + "r".encode() + source_desti_byte
    s.send(messege)
    
"""
The functions called when "watchdog" recognize that file or directory was created
in the monitered folder.
The function callong "sendCteateUpdate" to send information about the creating to the server.
"""

def on_created(event):
    if (observer_flag == 0):
        return
    #if (event.src_path[-4:] == '.swp'):
    #    return
    if ('.goutputstream-' in event.src_path):
        return
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server_ip, server_port))
    is_dir = event.is_directory
    sendCreateUpdate(s, event.src_path, is_dir)
    s.close()

"""
The functions called when "watchdog" recognize that file or directory was deleted
in the monitered folder.
The function callong "sendDeleteUpdate" to send information and instuction to the server.
"""
def on_deleted(event):
    if (observer_flag == 0):
        return
    #if (event.src_path[-4:] == '.swp'):
    #    return
    if ('.goutputstream-' in event.src_path):
        return
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server_ip, server_port))
    is_dir = event.is_directory
    sendDeleteUpdate(s, event.src_path, is_dir)
    s.close()

"""
The functions called when "watchdog" recognize that file or directory was modified
in the monitered folder.
"""
def on_modified(event):
    global modified_flag
    if (observer_flag == 0 or modified_flag == 1):
        return
    #if platform == "win32" and os.path.isfile(event.src_path):
    #    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #    s.connect((server_ip, server_port))
    #    sendDeleteUpdate(s, event.src_path, False)
    #    sendCreateUpdate(s, event.src_path, False)
    #    s.close()
        


"""
The functions called when "watchdog" recognize that file or directory was moved (or renamed)
in the monitered folder.
The function callong "sendMoveUpdate" to send information and instruction to the server.
"""
def on_moved(event):
    if (observer_flag == 0):
        return
    if ('.goutputstream-' in event.src_path):
        deleteCreate(event.dest_path)
        return
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server_ip, server_port))
    sendMoveUpdate(s, event.src_path, event.dest_path)
    s.close()


def normPath(path):
    if (os.sep == '/'):
        return path.replace('\\', '/')
    if (os.sep == '\\'):
        return path.replace('/', '\\')

def deleteCreate(path):
    my_file = open(path , 'rb')
    file_cn = my_file.read()
    my_file.close()
    os.remove(path)
    my_file = open(path , 'wb')
    my_file.write(file_cn)
    my_file.close()

"""
In this function we are sync all the information between server and client both sides 
if any changed is happend the client let the server know and the server update all the files 
that changed or removed
"""

def fullSync(sock, folder):
    list_size = int.from_bytes(sock.recv(4),"little")
    dir_list = deserializeList(sock.recv(list_size))
    dict_size = int.from_bytes(sock.recv(4),"little")
    file_dict = recvHelp(sock,dict_size)
    file_dict = deserializeDict(file_dict)
    for i in dir_list:
        i = normPath(i)
        if not os.path.exists(folder+i):
            os.makedirs(folder+i)
    for key in file_dict:
        #if not os.path.exists(folder+key):
        #    os.mknod(folder + key)
        norm_key = normPath(key)
        my_file = open(folder + norm_key , 'wb')
        my_file.write(file_dict[key])
        my_file.close()


"""
In this function we give the option to remove a folder of client
we go throgh all the files in this folder and remove them also

"""

def removeFolder(folder):
    for root, dirs, files in os.walk(folder, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))

"""
This finction handle all the process of exsist client 
get update of create \ delete \ modify or move any file 
protocol:
1) 'a' for the server to know this is exists client. 
2) id number for the server.
3) pc id for the server.

then the server send the stack update for this particular pc. for every command in the stack
the client will process the information and follow the instruction. 
'c' - for create command.
'd' - for delete command.
'm' - for modified command.
'r' - for moved command (replace)
"""

def existsClient(s):
    global observer_flag
    messege = "a".encode() + id_number.encode() + pc_id.encode()
    s.send(messege)

    stack = int.from_bytes(s.recv(4),"little")
    while(stack):
        observer_flag = 0
        command = s.recv(1).decode()
        # created
        if (command == 'c'):
            clientCreate(s)        

        # deleted
        if (command == 'd'):
            clientDelete(s)
        #modified
        if (command == 'm'):
            clientModified(s)
        # moved (replaced)
        if (command == 'r'):
            clientMove(s)
        stack = stack - 1
        observer_flag = 1

"""
Loading the data from the folder, all dirs into list.
and all files and their content into dict.
"""

def updateData(my_folder):
    for root, directories, files in os.walk(my_folder, topdown=False):
	    for name in directories:
             x = os.path.join(root, name)
             dir_list.append(x[base:])


    for root, directories, files in os.walk(my_folder, topdown=False):
	    for name in files:
             y = os.path.join(root, name)
             file_name = y[base:]
             if (file_name == "/client.py"):
                 continue
             f = open(y, "rb")
             files_dict[y[base:]] = f.read()
             f.close()

"""
Here we send all the information to Server from the 'files_dict' and 'dir_list'
"""

def sendAllToServer(s, header=""): 
    string_dict = serializeDict(files_dict)
    string_list = serializeList(dir_list)
    s.send(header.encode() + pc_id.encode() + len(string_list).to_bytes(4, "little") + string_list + len(string_dict).to_bytes(4, "little"))
    s.send(string_dict)

"""
An aid function to recieve from the buffer.
"""

def recvHelp(sock,size):
    originsize = size
    data = b''
    recieved = 0
    #if (size < 1024):
    #    data = data + sock.recv(size)
    #    return data
    #while (size > 1024):
    #    data = data + sock.recv(1024)
    #    recieved = recieved + 1024
    #    size = size - 1024
    #data = data + sock.recv(size)
    while (len(data) < originsize):
        data = data + sock.recv(originsize - len(data))
    return data


"""
Watchdog initialization.
"""
my_event_handler = PatternMatchingEventHandler(["*"], None, False, True)
my_event_handler.on_created = on_created
my_event_handler.on_deleted = on_deleted
my_event_handler.on_modified = on_modified
my_event_handler.on_moved = on_moved
observer = Observer()
observer.schedule(my_event_handler, my_folder, recursive=True)


"""
Initialize folder and update server in case of new client. 
Otherwize, if the client exists recieving information from the server to fill the folder.
"""

if(len(str(id_number)) == 1):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server_ip, server_port))
    updateData(my_folder)
    sendAllToServer(s, "b")
    id_number = s.recv(128).decode()
    s.close()
else:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server_ip, server_port))
    messege = "d".encode() + id_number.encode() + pc_id.encode()
    s.send(messege)
    fullSync(s, my_folder)
    s.close()



"""
The main loop, used for getting update from the server every "update_time" seconds. 
"""
observer.start()
while (True):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((server_ip, server_port))
    observer_flag = 1
    existsClient(s)
    s.close()
    time.sleep(0.001)
    time.sleep(int(update_time))