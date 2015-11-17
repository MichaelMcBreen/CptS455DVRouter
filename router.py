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

def recieve(sock):
    return sock.recv(2048).decode()


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
    
    print ('Setting Up Sockets . . .')
    baseDict, sockDict = setupSockets(routerName, rtrTable, linkTable)

    loopTime = 5
    while 1:
        start = time.time()
        sent = []
        sockList = list(sockDict.values())
        rReady, wReady, eReady = select.select(sockList, sockList, sockList, loopTime)
        # !!!!!!!!!!!!!!!!!!! need to read baseport sockets too
        
        # timeout handling
        if len(rReady) == 0:
            print ("Timeout Error: No available sockets")
        # read available messages
        else:
            for rName in sockDict:
                if sockDict[rName] in rReady:
                    msg = recieve(sockDict[rName])
                    if len(msg) > 0:
                        print('Updating DVTable: ', msg)
                        msg = DVUpdateMessage(rName, m)
                        sockDict[rName].send(msg.encode())
                        sent.append(rName)
                    else:
                        print("no data")    

        # send updated DVtable to all available neighbors
        for rName in sockDict:
            if rName not in sent:
                message = routerName + "Hello\n"
                print('Send : ', message)
                sockDict[rName].send(message.encode())
                resetSocket(routerName, rtrTable, linkTable, sockDict, rName)

        # updates sent every 30 seconds
        end = time.time()
        t = loopTime - end + start
        print('TIMER: (start=', start, ") (end=", end, ") (time=", t, ")")
        if t > 0:
            time.sleep(t)

# setup sockets
def setupSockets(localName, rtrTable, linkTable):
    #initalize address_in/out, unconnected inputs/ output dictionaries
    print('-----inside setup_sockets()')
    sockDict = {}
    baseDict = {}

    # setup baseport
    bFD = rtrTable[localName].baseport
    bSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    bSocket.setblocking(False)
    bSocket.bind((rtrTable[localName].host, bFD))
    baseDict[localName] = bSocket

    # setup neighbors
    for remoteName in linkTable:
        # router's base + locallink
        iFD = rtrTable[localName].baseport + linkTable[remoteName].locallink
        oFD = rtrTable[remoteName].baseport + linkTable[remoteName].remotelink
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.setblocking(False)
        s.bind((rtrTable[localName].host, iFD))
        s.connect((rtrTable[remoteName].host, oFD))
        sockDict[remoteName] = s        
    return  baseDict, sockDict

def resetSocket(localName, rtrTable, linkTable, sockDict, sockName):
    iFD = rtrTable[localName].baseport + linkTable[sockName].locallink
    oFD = rtrTable[sockName].baseport + linkTable[sockName].remotelink
    sockDict[sockName].close()
    sockDict[sockName] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sockDict[sockName].bind((rtrTable[localName].host, iFD))
    sockDict[sockName].connect((rtrTable[sockName].host, oFD))


def printFDList(socketDict, servSock):
    print("printing sockets")
    for entry in socketDict:
        print(entry, servSock[entry])


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
    
