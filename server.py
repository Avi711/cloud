import os
import string
import random
import socket
import time
import sys
from sys import platform
#port = 33333
try:
    port = int(sys.argv[1])
except:
    sys.exit()
# checking if port is valid. 
if (len(str(port)) != 5 or int(port) > 65535 or int(port) < 0):
    exit()
folder_count = int('1')
clients = dict()
my_path = os.getcwd()
update_struct = {}
move_stack = []
def createNewId():
    
    while(1):
        temp=(''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(128)))
        flag=0
        for key in clients:
            if(key==temp):
                flag=1
                break
        if(flag==0):
            return temp    
                

def updateData(source_folder):
    dir_list = []
    files_dict = {}
    base = len(source_folder)
    for root, directories, files in os.walk(source_folder, topdown=False):
	    for name in directories:
             x = os.path.join(root, name)
             dir_list.append(x[base:])


    for root, directories, files in os.walk(source_folder, topdown=False):
	    for name in files:
             y = os.path.join(root, name)
             file_name = y[base:]
             if (file_name == os.sep + "test.py"):
                 continue
             f = open(y, "rb")
             files_dict[y[base:]] = f.read()
             f.close()
    return (dir_list, files_dict)


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

def serializeDict(file_dict):
    data = b''
    for key in file_dict:
        data = data + len(key.encode()).to_bytes(4, "little")
        data = data + key.encode()
        data = data + len(file_dict[key]).to_bytes(4, "little")
        data = data + file_dict[key]
    return data


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

def serializeList(file_dict):
    data = b''
    for key in file_dict:
        data = data + len(key.encode()).to_bytes(4, "little")
        data = data + key.encode()
    return data



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


def normPath(path):
    if (os.sep == '/'):
        return path.replace('\\', '/')
    if (os.sep == '\\'):
        return path.replace('/', '\\')

def fullSync(sock, folder):
    list_size = int.from_bytes(sock.recv(4),"little")
    dir_list = sock.recv(list_size)
    dir_list = deserializeList(dir_list)
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
function called when needed to create new client.
generate random number for particular pc, and random number for the client id. 
creating a stakc update for the particular pc. 
and then full sync from the folder of the client into new folder which will belong to this client id. 
"""


def createNewClient(current_folder):
    pc_id = client_socket.recv(50).decode()
    id=createNewId()
    print(id)
    client_socket.send(id.encode())
    clients[id]= str(current_folder)
    while os.path.exists(my_path+ os.sep + str(current_folder)):
        current_folder = current_folder + 1
    os.makedirs(my_path+ os.sep + str(current_folder))
    fullSync(client_socket,(my_path + os.sep + str(current_folder)))

    client_stack =  []
    update_struct[str(id) + pc_id] = client_stack
    return current_folder + 1

"""
Function called when exists client want to get updated. 
the function access the patricular stack of this client and pc, and send the stack update to the pc. 
"""


def existingClient(id, pc_id):
    client_stack = update_struct[str(id) + pc_id]
    client_socket.send(len(client_stack).to_bytes(4, "little"))
    while (len(client_stack) > 0):
        client_socket.send(client_stack.pop(0))

"""
Function called when exists client connect from new pc. 
the server will send him the content of his folder and will create for this pc new stack command 
for future updates. 
"""    

def newComputerClient(id):
    client_stack =  []
    update_struct[str(id) + pc_id] = client_stack
    (dir_list, files_dict) = updateData(my_path + os.sep + str(clients[id]))
    sendAllToClient(dir_list, files_dict)



def sendAllToClient(dir_list, files_dict):   
    string_dict = serializeDict(files_dict)
    string_list = serializeList(dir_list)
    messege = len(string_list).to_bytes(4, "little") + string_list + len(string_dict).to_bytes(4, "little")
    client_socket.send(messege)
    client_socket.send(string_dict)

"""
Function used to insert a command to all the pc's of client. 
"""  

def addToStack(command):
    for key in update_struct:
        if key[0:128] == client_id and key[128:] != pc_id:
            update_struct[key].append(command)



def clientCreate(c_folder):
    c_type = client_socket.recv(1).decode()
    length = int.from_bytes(client_socket.recv(4),"little")
    if (c_type == 'd'):
        create_path = client_socket.recv(length).decode()
        create_path = normPath(create_path)
        if not os.path.exists(c_folder + create_path):
            os.makedirs(c_folder + create_path)
        stack_command = "c".encode() + c_type.encode() + length.to_bytes(4,"little") + create_path.encode()
        addToStack(stack_command)
    if (c_type == 'f'):
        f_name = (client_socket.recv(length)).decode()
        f_name = normPath(f_name)
        length_content = int.from_bytes(client_socket.recv(4),"little")
        #f_content = (client_socket.recv(length_content))
        f_content = recvHelp(client_socket,length_content)
        #if not os.path.exists(c_folder + f_name):
            #os.mknod(c_folder + f_name)
        my_file = open(c_folder + f_name, 'wb')
        my_file.write(f_content)
        stack_command = "c".encode() + c_type.encode() + length.to_bytes(4, "little") + f_name.encode() + length_content.to_bytes(4,"little") + f_content
        addToStack(stack_command)
        my_file.close()

def clientDelete(c_folder):
    c_type = client_socket.recv(1).decode()
    length = int.from_bytes(client_socket.recv(4),"little")
    delete_path = client_socket.recv(length).decode()
    delete_path = normPath(delete_path)
    if (os.path.isdir(c_folder + delete_path)):
        if os.path.exists(c_folder + delete_path):
            removeFolder(c_folder + delete_path)
            os.rmdir(c_folder + delete_path)
        stack_command = "d".encode() + c_type.encode() + length.to_bytes(4, "little") + delete_path.encode()
    else:
        if os.path.exists(c_folder + delete_path):
            os.remove(c_folder + delete_path)
    stack_command = "d".encode() + c_type.encode() + length.to_bytes(4, "little") + delete_path.encode()
    addToStack(stack_command)

def removeFolder(folder):
    for root, dirs, files in os.walk(folder, topdown=False):
        for name in files:
            os.remove(os.path.join(root, name))
        for name in dirs:
            os.rmdir(os.path.join(root, name))


def clientModified(c_folder):
    return


def clientMove(c_folder):
    length_src = int.from_bytes(client_socket.recv(4),"little")
    src = client_socket.recv(length_src).decode()
    src = normPath(src)
    length_dest = int.from_bytes(client_socket.recv(4),"little")
    desti = client_socket.recv(length_dest).decode()
    desti = normPath(desti)
    if(os.path.exists(c_folder + src)):
        try:
            os.replace(c_folder + src, c_folder + desti)
            stack_command = "r".encode() + length_src.to_bytes(4, "little") + src.encode() + length_dest.to_bytes(4, "little") + desti.encode()
            addToStack(stack_command)
            moveStackHandle()
        except:
            move_stack.append((c_folder + src,c_folder + desti))


def moveStackHandle():
    while(move_stack):
        tup = move_stack.pop()
        if(os.path.exists(tup[0])):
            os.replace(tup[0], tup[1])
            stack_command = "r".encode() + len(tup[0]).to_bytes(4, "little") + tup[0].encode() + len(tup[1]).to_bytes(4, "little") + tup[1].encode()
            addToStack(stack_command)



def clientCommand(id):
    c_folder = str(clients[id])
    command = client_socket.recv(1).decode()
    # created
    if (command == 'c'):
        clientCreate(c_folder)        

    # deleted
    if (command == 'd'):
        clientDelete(c_folder)
    #modified
    if (command == 'm'):
        clientModified(c_folder)
    # moved (replaced)
    if (command == 'r'):
        clientMove(c_folder)
    
    #if (client_socket.recv(1).decode == 'a'):
    #    existingClient(id)

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', port))
server.listen(1000)

"""
Main loop.
Protocol:
'a' - for exists client. (when the client want to get updated).

'b' - for new client. creating new client. 

'c' - for client command. (when the client want to make change in his folder).

'd' - for new pc. when the client connect from new computer and wants to sync this computer with his folder.

"""

while True:
    client_socket, client_address = server.accept()
    data = client_socket.recv(1)
    if (data.decode() == 'a'):
        client_id = client_socket.recv(128).decode()
        pc_id = client_socket.recv(50).decode()
        existingClient(client_id, pc_id)

    if(data.decode() == 'b'):
        folder_count = createNewClient(folder_count)

    if(data.decode() == 'c'):
        client_id = client_socket.recv(128).decode()
        pc_id = client_socket.recv(50).decode()
        clientCommand(client_id)
    if (data.decode() == 'd'):
        client_id = client_socket.recv(128).decode()
        pc_id = client_socket.recv(50).decode()
        newComputerClient(client_id)

    
    client_socket.close()