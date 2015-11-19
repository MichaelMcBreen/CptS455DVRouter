import string
import socket
import sys
import select
import time
import re

# these are global varibles, yes we know this is bad
DVTable = {} # Dictionary of Dictionaries
RouterList = []
SelfName = "Not Set"
PoisonReverse = True

class RouterInfo:
    def __init__(self, host, baseport):
        self.host, self.baseport = host, baseport;

class LinkInfo:
    def __init__(self, cost, locallink, remotelink):
        self.cost, self.locallink, self.remotelink = cost, locallink, remotelink;

class ServSockInfo:
    def __init__(self,socket, baseport):
        self.socket, self.baseport = socket, baseport;    

# provided by Hauser
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

# provided by Hauser
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

# returns info from the socket
def recieve(sock):
    return sock.recv(2048).decode()

# a function I use to quickly test
# Is not called when used by command line
def main():
    dvsimulator(["router.py", "-p", "test1", "A"])

# builds the inital DVTable
def BuildTable(rtrTable, linkTable):
    # Create Table
    for router in rtrTable:
        RouterList.append(str(router))
    RouterList.sort()
    # Initialize table to infinity
    for dest in RouterList:
        row = {}
        for firstHop in RouterList:
            row[firstHop] = 64
        DVTable[dest] = row
    # Sets connection to self as 0
    DVTable[SelfName][SelfName] = 0
    # Sets inital costs
    for entry in linkTable:
        DVTable[entry][entry] = linkTable[entry].cost

# main simulation
def dvsimulator(argv):
    print("staring DV simulator")
    # if set proper arguments from argv
    if(len(argv) == 4):
        poption = True
        testDirName = argv[2]
        routerName = argv[3]
    else:
        poption = False
        testDirName = argv[1]
        routerName = argv[2]
    
    global SelfName

    SelfName = str(routerName)
    # load data for router and link tables
    rtrTable = readrouters(testDirName)
    linkTable = readlinks(testDirName,routerName)
    # initialize DV Table
    BuildTable(rtrTable, linkTable)
    dvtable = {}
    # setup sockets for read/write
    baseDict, sockDict = setupSockets(routerName, rtrTable, linkTable)
    # loopTime = 30
    loopTime = 1
    while 1:
        start = time.time()
        baseList = list(baseDict.values())
        sockList = list(sockDict.values())
        rReady, wReady, eReady = select.select(baseList + sockList, sockList, sockList, loopTime)
        # timeout no sockets to read from
        if len(rReady) == 0:
            a = 1
            # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!print ("Timeout Error: No available sockets")
        else:
            # read update messages from baseport and neighbor sockets
            readUpdates(routerName, rReady, rtrTable, linkTable, baseDict, sockDict)
        # send update messages to neighbor sockets
        sendUpdates(routerName, poption, rtrTable, linkTable, baseDict, sockDict)
        # print the DV Table
        # PrintDVTable()
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

# read messages from baseport and neighbor sockets
def readUpdates(routerName, rReady, rtrTable, linkTable, baseDict, sockDict):
    # read from neighbor sockets
    for rName in sockDict:
        if sockDict[rName] in rReady:
            msg = recieve(sockDict[rName])
            if len(msg) > 0:
                #!!!!!!!!!!!!!!!!!!!!print('Recv MSG ', rName, ' : ', msg)
                DVUpdateMessage(rName, msg)
    # read from baseport sockets
    for rName in baseDict:
        if baseDict[rName] in rReady:
            msg = recieve(baseDict[rName])
            if len(msg) > 0:
                #!!!!!!!!!!!!!!!!!!!!!!!!!!!!print('Recv MSG ', rName, ' : ', msg)
                DVUpdateMessage(rName, msg)

# send DVTable update message to neighbors
def sendUpdates(routerName, poption, rtrTable, linkTable, baseDict, sockDict):
    for rName in sockDict:
        if poption:
            message = BuildUMessagePoison(rName)
        else:
            message = BuildUMessage()
        #!!!!!!!!!!!!!!!!!!!print('Send To ', rName, ' : ', message)
        sockDict[rName].send(message.encode())
        resetSocket(routerName, rtrTable, linkTable, sockDict, rName)

# setup sockets
def setupSockets(localName, rtrTable, linkTable):
    # initalize address_in/out, unconnected inputs/ output dictionaries
    sockDict = {}
    baseDict = {}
    # setup baseport
    bFD = rtrTable[localName].baseport
    bSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    bSocket.bind((rtrTable[localName].host, bFD))
    baseDict[localName] = bSocket
    # setup neighbors
    for remoteName in linkTable:
        # router's base + locallink
        iFD = rtrTable[localName].baseport + linkTable[remoteName].locallink
        oFD = rtrTable[remoteName].baseport + linkTable[remoteName].remotelink
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind((rtrTable[localName].host, iFD))
        s.connect((rtrTable[remoteName].host, oFD))
        sockDict[remoteName] = s        
    return  baseDict, sockDict

# resets socket by closing then creating a new socket
def resetSocket(localName, rtrTable, linkTable, sockDict, sockName):
    iFD = rtrTable[localName].baseport + linkTable[sockName].locallink
    oFD = rtrTable[sockName].baseport + linkTable[sockName].remotelink
    sockDict[sockName].close()
    sockDict[sockName] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sockDict[sockName].bind((rtrTable[localName].host, iFD))
    sockDict[sockName].connect((rtrTable[sockName].host, oFD))

# prints out the DV Table
def PrintDVTable():
    # prints top first hop column labels for table
    print("\nPrinting DVTable")
    print("from", SelfName,":", end=" ")
    for firstHop in RouterList:
        print("via" , firstHop, end="  ")
    print()
    # prints start of row
    for dest in RouterList:
        print("to  ", dest, end= " :  ")
        # prints each entry in a row
        for firstHop in RouterList:
            cost = DVTable[dest][firstHop]
            if(cost == 64):
                cost = "INF"
            print(repr(cost).rjust(5), end="  ")
        print()
    print()

# prints out the routing table
def PrintRoutingTable():
    print("\nPrinting Routing Table")
    tableLines = {}
    for dest in DVTable:
        leastCost = 64
        firstHop = SelfName
        # print each row of routing table
        for nextHop in DVTable[dest]:
            if leastCost > DVTable[dest][nextHop]:
                leastCost = DVTable[dest][nextHop]
                firstHop = nextHop
        tableLines[dest] = SelfName + " - dest: " + dest + " cost: " + str(leastCost) + " nexthop: " + firstHop
    for dest in RouterList:
        if dest in tableLines:
            print(tableLines[dest])
    print()

# prints a routing table entry
def PrintLinkChanges(dest, cost, nexthop):
    print(SelfName, "- dest:", dest, "cost:", str(cost), "nexthop:",nexthop)

# updates DV Table with message received from router From
def DVUpdateMessage(From, Message):
    # handle U messages
    if Message[0] == "U":
        Updates = Message.split(" ")
        # remove the 'U'
        Updates = Updates[1:len(Updates)]
        Values = {}
        # load each update into router and cost
        for i in range(0,int(len(Updates)/2)):
            Values[Updates[2*i]] = int(Updates[2*i + 1])
        # Update the from column
        for dest in RouterList:
            currentValue = DVTable[dest][From]
            # Sets to row from From to the lowest cost to get to From + cost from From to
            DVTable[dest][From] = DVTable[From][From] + Values[dest]
            # costs above 64 are set back to 64 for infinity
            if(DVTable[dest][From] > 64):
                DVTable[dest][From] = 64
            if(DVTable[dest][From] != currentValue):
                b = 1
                #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!PrintLinkChanges(dest, DVTable[dest][From], From)
    # handle L and P messages
    else:
        ParseMessage(Message)

# gets the lowest cost to a router
def GetLowestCostForRouter(dest):
    lowestCost = 64
    for firstHop in DVTable[dest]:
        if(DVTable[dest][firstHop] < lowestCost):
            lowestCost = DVTable[dest][firstHop]
    return lowestCost

# build a regular U message
def BuildUMessage():
    Message = "U"
    for dest in RouterList:
        Message = Message + " " + dest + " " + str(GetLowestCostForRouter(dest))
    return Message

# If we must go through another router to get to the destination we tell that neighbor
# that we have an infinate cost to get to it
def BuildUMessagePoison(firstHop):
    Message = "U"
    for dest in RouterList:
        # if the lowest cost to get to a another router than we say it cost infinate
        if(dest != firstHop and GetLowestCostForRouter(dest) == DVTable[dest][firstHop]):
            Message = Message + " " + dest + " " + str(64)
        else:
            Message = Message + " " + dest + " " + str(GetLowestCostForRouter(dest))
    return Message

# parses incoming messages to base router  
def ParseMessage(Message):
    msgType = Message[0]
    # handle L message
    if(msgType == "L"):
        ParseLMessage(Message)
    # handle P message
    else:
        PrintRoutingTable()

# parses L messages
def ParseLMessage(Message):
    parts = Message.split(" ")
    currentValue = DVTable[parts[1]][parts[1]]
    DVTable[parts[1]][parts[1]] = int(parts[2])
    if(currentValue != DVTable[parts[1]][parts[1]]):
        PrintLinkChanges(parts[1], DVTable[parts[1]][parts[1]], parts[1])

# Calls DVSimulator with cmd argv
dvsimulator(sys.argv)
    
