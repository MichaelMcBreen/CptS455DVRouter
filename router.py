import string
import socket
import sys
import random
import select
import time
import re

#these are global varibles, yes we know this is bad
RouterTable = {} #Dictionary of Dictionary
RouterList = []
SelfName = "Not Set"
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

#provided by Hauser
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

#provided by Hauser
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

#returns info from the socket
def recieve(sock):
    return sock.recv(2048).decode()

#a function I use to quickly test
#Is not called when used by command line
def main():
    dvsimulator(["router.py", "-p", "test1", "A"])

#builds the inital routerTable
def BuildTable(rTable, linkTable):
    for router in rTable:
        RouterList.append(str(router))
    RouterList.sort()
    
    for router in RouterList:
        row= {}
        #sets table to all infinate
        for entry in RouterList:
            row[entry] = 64
        RouterTable[router] = row
    #sets connection to self as 0
    RouterTable[SelfName][SelfName] = 0
    #sets inital costs
    for entry in linkTable:
        RouterTable[entry][entry] = linkTable[entry].cost
        
    PrintRoutingTable(RouterTable)

#our main simulation
def dvsimulator(argv):
    print("staring DV simulator")
    print(argv, len(argv))
    #if p option
    if(len(argv) == 4):
        poption = True
        testDirName = argv[2]
        routerName = argv[3]
    else:
        poption = False
        testDirName = argv[1]
        routerName = argv[2]
    
    print(poption, testDirName, routerName)
    global SelfName

    SelfName = str(routerName)
    
    rtrTable = readrouters(testDirName)
    linkTable = readlinks(testDirName,routerName)
    BuildTable(rtrTable, linkTable)
    dvtable = {}
    
    #open up output file to log
    f = open("output" + routerName + ".txt", 'w')
    baseDict, sockDict = setupSockets(routerName, rtrTable, linkTable)
    
    # loopTime = 30
    loopTime = 10
    while 1:
        start = time.time()
        baseList = list(baseDict.values())
        sockList = list(sockDict.values())
        rReady, wReady, eReady = select.select(baseList + sockList, sockList, sockList, loopTime)
        
        # timeout no sockets to read from
        if len(rReady) == 0:
            print ("Timeout Error: No available sockets")
        else:
            # read update messages from baseport and neighbor sockets
            readUpdates(routerName, rReady, rtrTable, linkTable, baseDict, sockDict)

        # send update messages to neighbor sockets
        sendUpdates(routerName, poption, rtrTable, linkTable, baseDict, sockDict)

        
        PrintRoutingTable(RouterTable)
    


        # timer to loop every 30 seconds
        end = time.time()
        t = loopTime - end + start
        while t > 0:
            time.sleep(1)
            # check for triggered updates to baseport sockets
            rReady, wReady, eReady = select.select(baseList, baseList, baseList)
            if len(rReady) > 0:
                break

            t = t - 1
    f.close()

# read messages from baseport and neighbor sockets
def readUpdates(routerName, rReady, rtrTable, linkTable, baseDict, sockDict):
    # read from neighbor sockets
    for rName in sockDict:
        if sockDict[rName] in rReady:
            msg = recieve(sockDict[rName])
            if len(msg) > 0:
                print('Recv MSG ', rName, ' : ', msg)
                DVUpdateMessage(rName, msg)
    # read from baseport sockets
    for rName in baseDict:
        if baseDict[rName] in rReady:
            msg = recieve(baseDict[rName])
            if len(msg) > 0:
                print('Recv MSG ', rName, ' : ', msg)
                DVUpdateMessage(rName, msg)

# send DVTable update message to neighbors
def sendUpdates(routerName, poption, rtrTable, linkTable, baseDict, sockDict):
    for rName in sockDict:
        if poption:
            message = BuildUMessagePosion(rName)
        else:
            message = BuildUMessage()
        print('Send To ', rName, ' : ', message)
        sockDict[rName].send(message.encode())
        resetSocket(routerName, rtrTable, linkTable, sockDict, rName)

# setup sockets
def setupSockets(localName, rtrTable, linkTable):
    #initalize address_in/out, unconnected inputs/ output dictionaries
    print('-----inside setup_sockets()')
    sockDict = {}
    baseDict = {}

    # setup baseport
    bFD = rtrTable[localName].baseport
    bSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #bSocket.setblocking(False)
    bSocket.bind((rtrTable[localName].host, bFD))
    baseDict[localName] = bSocket

    # setup neighbors
    for remoteName in linkTable:
        # router's base + locallink
        iFD = rtrTable[localName].baseport + linkTable[remoteName].locallink
        oFD = rtrTable[remoteName].baseport + linkTable[remoteName].remotelink
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        #s.setblocking(False)
        s.bind((rtrTable[localName].host, iFD))
        s.connect((rtrTable[remoteName].host, oFD))
        sockDict[remoteName] = s        
    return  baseDict, sockDict

#resets socket
def resetSocket(localName, rtrTable, linkTable, sockDict, sockName):
    iFD = rtrTable[localName].baseport + linkTable[sockName].locallink
    oFD = rtrTable[sockName].baseport + linkTable[sockName].remotelink
    sockDict[sockName].close()
    sockDict[sockName] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sockDict[sockName].bind((rtrTable[localName].host, iFD))
    sockDict[sockName].connect((rtrTable[sockName].host, oFD))

#prints out the FD list
def printFDList(socketDict, servSock):
    print("printing sockets")
    for entry in socketDict:
        print(entry, servSock[entry])

#prints out the routing table
def PrintRoutingTable(Table):
    ##prints top label for table
    print("Printing Table")
    print("from", SelfName,":", end=" ")
    for routerName in RouterList:
        print("via" , routerName, end="  ")
    print()
    "prints start of row"
    for routerName in RouterList:
        print("to  ", routerName, end= " :  ")
        #prints each entry in a row
        for entry in RouterList:
            printedCost = Table[routerName][entry]
            if(printedCost == 64):
                printedCost = "INF"
            print(repr(printedCost).rjust(5), end="  ")
        print()

#updates routing table from received update
def DVUpdateMessage(From, Message):
    
    if Message[0] == "U":
        #changesMade = False
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
            currentValue = RouterTable[rows][From]
            RouterTable[rows][From] = RouterTable[From][From] + Values[rows]
            if(RouterTable[rows][From] > 64):
                RouterTable[rows][From] = 64
            if(RouterTable[rows][From] != currentValue):
                PrintLinkChanges(rows,RouterTable[rows][From],From)
    else:
        ParseMessage(Message)

#gets the lowest cost to a router
def GetLowestCostForRouter(Router):
    lowestCost = 64
    for entry in RouterTable[Router]:
        if(RouterTable[Router][entry] < lowestCost):
            lowestCost = RouterTable[Router][entry]
    return lowestCost

#selection which type of message to create
def SendUMessage():
    Message = ""
    if(PosionReverse):
        Message = BuildUMessagePosion("B")
    else:
        Message = BuildUMessage()
    print("Creating U Message")
    print(Message)
    #SendToAllNeighbor(Message)

#build a regulay U message
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

#parses incoming messages to base router  
def ParseMessage(Message):
    MessageType = Message[0]
    if(MessageType == "L"):
        ParseLMessage(Message)
    else:
        ParsePMessage(Message)

#parses L messages
def ParseLMessage(Message):
    print("Incoming L message: ", Message)
    parts = Message.split(" ")
    currentValue = RouterTable[parts[1]][parts[1]]
    RouterTable[parts[1]][parts[1]] = int(parts[2])
    if(currentValue != RouterTable[parts[1]][parts[1]]):
        PrintLinkChanges(parts[1],RouterTable[parts[1]][parts[1]],parts[1])

#parses P messages
def ParsePMessage(Message):
    print("Income P Message")
    if(len(Message) == 1):
        PrintRoutingTable(RouterTable)
    else:
        PrintDestination(Message[2])

#prints out the Destination        
def PrintDestination(Destination):
    print("Printing Entries for Destination: ", Destination, end=" ")
    for entry in RouterList:
        print(entry,RouterTable[Destination][entry], end=" ")
    print()

def PrintLinkChanges(dest, cost, nexthop):
    print(SelfName, " - dest:", dest, " cost:", cost, " nexthop:",nexthop)

#Calls DVSimulator with cmd argv
dvsimulator(sys.argv)
    
