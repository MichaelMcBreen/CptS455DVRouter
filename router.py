import string
import socket
import sys
import random
import select
import time
import re

#everything is global till we create more of an outline
RouterTable = {} #Dictionary of Dictionary
RouterList = ["A", "B", "C", "D"]
SelfName = "A"
PosionReverse = True

class RouterInfo:
    def __init__(self, host, baseport):
        self.host, self.baseport = host, baseport;

class LinkInfo:
    def __init__(self, cost, locallink, remotelink):
        self.cost, self.locallink, self.remotelink = cost, locallink, remotelink;

class ServSockInfo:
    def __init__(self,socket, baseport):
        self.socket, self.baseport = socket, baseport;    
        
def readrouters(testname):
    f = open(testname+'/routers')
    lines = f.readlines()
    table = {}
    for line in lines:
        if line[0]=='#': continue
        #print line
        words = line.split(" ")    
        table[words[0]] = RouterInfo(words[1], int(words[2]))

    f.close()
    return table


# make the set empty
def FD_ZERO(setFDs):
    del setFDs[:]

# includes fd in the set
def FD_SET (fd, setFDs):  
    setFDs.append(fd)
    setFDs.sort();

# remove fd from the set
def FD_CLR (fd, setFDs):
    setFDs.remove(fd)

# returns 1 if fd is in the set, 0 if not
def FD_ISSET (fd, setFDs):
    if(fd in setFDs):
        return 1
    else:
        return 0

def readAll(sock):
    data = []
    while True:
        chunk = sock.recv(2048)
        if not chunk: break
        data.append(chunk)
    return ''.join(data)

def msgSplit(data):
    messages = []
    j = 0
    i = 0
    while i < len(data):
        j = i + 1
        while j < len(data) and not (j == len(data) or str(data[j]) == 'U' or str(data[j]) == 'L' or data[j:j+1] == 'P'):
            j = j + 1
        messages.append(data[i:j].strip(' '))
        i = j
    return messages

def main(argv):
    dvsimulator(argv)

def dvsimulator(argv):
    print ('----ENTERING dvsimulator-----')
    print("I am working", argv)
    testDirName = "Test1"
    routerName = "A"
    poption = False
    if(len(argv) == 3):
        poption = True
        testDirName = argv[3]
        routerName = argv[4]
    else:
        poption = False
        testDirName = argv[2]
        routerName = argv[3]
    print(poption, testDirName, routerName)
    
    print ('calling readrouters(testDirName)')
    rtrTable = readrouters(testDirName)
    linkTable = readlinks(testDirName,routerName)
    dvtable = {}
    
    #open up output file to log
    f = open(routerName + ".output", 'w')
    f.close()
    
    print ('Creating Sockets . . .')
    inputs, outputs, toConnInputs, toConnOutputs = create_sockets(routerName, rtrTable, linkTable)
    print ('Connecting Sockets . . .')
    connect_sockets(rtrTable, linkTable, inputs, outputs, toConnInputs, toConnOutputs)

    while 1:
        start = time.time()
        print("Looping at time: ", start)
        
        rReady, wReady, eReady = select.select(list(inputs.values()), list(outputs.values()), list(inputs.values()))

        # timeout handling
        if len(rReady) == 0:
            print ("Timeout Error: No available sockets")
        # read available messages
        else:
            for iName in rReady:
                # read all data in socket and parse messages
                data = readAll(s)
                print('Recv : ', data)
                messages = msgSplit(data)
                for m in messages:
                    DVUpdateMessage(servSock[s], m)
        # send updated DVtable to all available neighbors
        for s in wReady:
            # needs to modify for poison and specific messages
            # data = BuildUMessage()
            print('Send : ', 'Hello World')
            # send takes a BYTES object not STR
            s.send(b'Hello World')
        
        end = time.time()

        # updates sent every 30 seconds
        t = 30 - end + start
        if t >= 0 and t < 30: time.sleep(t)

# makes sockets
def create_sockets(routerName, rtrTable, linkTable):
    #initalize address_in/out, unconnected inputs/ output dictionaries
    print('-----inside create_sockets()')

    toConnInputs = []
    toConnOutputs = []
    inputs = {}
    outputs = {}

    bFD = rtrTable[routerName].baseport
    bSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    bSocket.setblocking(False)
    bSocket.bind((rtrTable[routerName].host, bFD))
    bSocket.listen(10)
    inputs[routerName] = bSocket    

    for rName in linkTable:
        # router's base + locallink
        iFD = rtrTable[routerName].baseport + linkTable[rName].locallink
        iSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        iSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        iSocket.setblocking(False)
        iSocket.bind((rtrTable[rName].host, iFD))
        iSocket.listen(5)
        toConnInputs.append(rName)
        
        # remote's base + remotelink
        oFD =  rtrTable[rName].baseport + linkTable[rName].remotelink
        oSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        toConnOutputs.append(rName)

        inputs[rName] = iSocket
        outputs[rName] = oSocket

    return  inputs, outputs, toConnInputs, toConnOutputs

def connect_sockets(rtrTable, linkTable, inputs, outputs, toConnInputs, toConnOutputs):
    print("--------inside connect_sockets()")
    print ('inputs : ', inputs)
    print ('outputs: ', outputs)
    while len(toConnInputs) + len(toConnOutputs) > 0:
        for oName in toConnOutputs:
            try:
                outputs[oName].connect((rtrTable[oName].host, rtrTable[oName].baseport + linkTable[oName].remotelink))
                print("Output Connected : ", oName)
                toConnOutputs.remove(oName)
            except socket.error:
                pass
        # passing dictionary inputs, outputs - do dictionaries work?
        rReady, wReady, eReady = select.select(list(inputs.values()), list(outputs.values()), [])
        
        for iSock in rReady:
            for iName in inputs:
                if inputs[iName] == iSock:
                    sock, addr = inputs[iName].accept()
                    print("Input Connected : ", iName)
                    inputs[iName] = sock
                    toConnInputs.remove(iName)

def printFDList(socketDict, servSock):
    print("printing sockets")
    for entry in socketDict:
        print(entry, servSock[entry])


def readlinks(testname, router):
    f = open(testname+'/'+router+'.cfg')
    lines = f.readlines()
    table = {}
    for line in lines:
        if line[0]=='#': continue
        words = line.split(" ")
        table[words[0]] = LinkInfo(int(words[1]), int(words[2]), int(words[3]))
    f.close()
    return table

def PrintRoutingTable(Table):
    ##prints top label for table
    print("Printing Table")
    print("from ", SelfName,":", end="")
    for routerName in RouterList:
        print(routerName, end="  ")
    print()
    "prints start of row"
    for routerName in RouterList:
        print("to   ", routerName, end= " : ")
        #prints each entry in a row
        for entry in RouterList:
            print(repr(Table[routerName][entry]).ljust(2), end=" ")
        print()

def DVUpdateMessage(From, Message):
    print("Incoming U Message from: ", From, " ", Message)
    print("Before")
    PrintRoutingTable(RouterTable)
    Updates = Message.split(" ")
    #remove the 'U'
    Updates = Updates[1:len(Updates)]
    Values = {}
    for i in range(0,int(len(Updates)/2)):
        #load each update into router and cost
        Values[Updates[2*i]] = int(Updates[2*i + 1])
    for rows in RouterList:
        #Update the from collumn
        #Sets to row from From to the lowest cost to get to From + cost from From to
        RouterTable[rows][From] = RouterTable[From][From] + Values[rows]
        if(RouterTable[rows][From] > 64):
            RouterTable[rows][From] = 64
    print("After")
    PrintRoutingTable(RouterTable)   

def GetLowestCostForRouter(Router):
    lowestCost = 64
    for entry in RouterTable[Router]:
        if(RouterTable[Router][entry] < lowestCost):
            lowestCost = RouterTable[Router][entry]
    return lowestCost

#have to update for posion reverse
def SendUMessage():
    Message = ""
    if(PosionReverse):
        Message = BuildUMessagePosion("B")
    else:
        Message = BuildUMessage()
    print("Creating U Message")
    print(Message)
    #SendToAllNeighbor(Message)

def BuildUMessage():
    Message = "U"
    for entry in RouterList:
        Message = Message + " " + entry + " " + str(GetLowestCostForRouter(entry))
    return Message
#If we must go through another router to get to the destination we tell that router
#that we have an infinate cost to get to it
def BuildUMessagePosion(router):
    Message = "U"
    for entry in RouterList:
        #if the lowest cost to get to a another router than we say it cost infinate
        if(entry != router and GetLowestCostForRouter(entry) == RouterTable[entry][router]):
            Message = Message + " " + entry + " " + str(64)
        else:
            Message = Message + " " + entry + " " + str(GetLowestCostForRouter(entry))
    return Message
    
def ParseMessage(Message):
    MessageType = Message[0]
    if(MessageType == "L"):
        ParseLMessage(Message)
    else:
        ParsePMessage(Message)

def ParseLMessage(Message):
    print("Incoming L message: ", Message)
    parts = Message.split(" ")
    RouterTable[parts[1]][parts[1]] = int(parts[2])

def ParsePMessage(Message):
    print("Income P Message")
    if(len(Message) == 1):
        PrintRoutingTable(RouterTable)
    else:
        PrintDestination(Message[2])
        
def PrintDestination(Destination):
    print("Printing Entries for Destination: ", Destination, end=" ")
    for entry in RouterList:
        print(entry,RouterTable[Destination][entry], end=" ")
    print()

#Calls DVSimulator with cmd argv
dvsimulator(sys.argv)
    
