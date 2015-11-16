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
    #print table.get('A')
    for x in table:
        print "router info: "
        attrs = vars(table[x])
        print ', '.join("%s: %s" % item for item in attrs.items())
             
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
    return fd in setFDs? 1 : 0

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

def dvsimulator(poption, testdirame, routerame):
    readFDs = []
    writeFDs = []
    exceptFDs = []
    servSock =  {}
    rlTable = {}
    print 'calling readrouters(testdirame)'
    table = readrouters(testdirame)
    dvtable = {}
    print '----ENTERING dvsimulator-----'
    print "poption : "+ poption
    print "testdirame : "+ testdirame
    print "routerame : "+ routerame
    #open up output file to log
    f = open(routerame + ".output", 'w')
    f.close()
    print '------------------------------------------------------------------>hey'
    mybaseport = table.get(routerame).baseport
    print table.get(routerame).baseport
    #we should set up the baseport to listen
    servSock[table.get(routerame).baseport] =ServSockInfo((makelisten(table.get(routerame).host, table.get(routerame).baseport)), mybaseport)
    #making router listen on its baseport
    #servSock["q"] =ServSockInfo("9000",mybaseport)
    print '------------------------------------------------------------------>baseport'
    print servSock.get(mybaseport).socket
    rlTable = readlinks(testdirame,routerame)

    for neighbor in rlTable:
        print 'neighbor[0] = '+neighbor[0]
        myreadfds = table.get(routerame).baseport + rlTable.get(neighbor[0]).locallink
        mywritefds = table.get(neighbor[0]).baseport + rlTable.get(neighbor[0]).remotelink
        print 'myreadfds: '+ str(mywritefds)
        #for each link in our read link table
            #make listen for our locallink
            #make socket for our outgoing link
        #save FDS into read FDs    
        readFDs.append(myreadfds) 
        #tell it to listen by on the offset
        print 'creating socket and bind with incoming port and set it to listen...'   
        servSock[myreadfds] = ServSockInfo(makelisten(table.get(routerame).host, myreadfds), table.get(routerame).baseport)
        print 'successfully created socket for listening'  
        #save socket into servSock dict with FDS as key and socket and output FDs are stored

        #save outgoing fds into writeFDs
        writeFDs.append(mywritefds)
        #now creating outgoing sockets
        print 'creating socket and bind with outgoing port...'
        servSock[mywritefds]  = ServSockInfo(makesend(table.get(neighbor[0]).host, mywritefds),table.get(neighbor[0]).baseport)
        print 'successfully return outgoing socket...'

        for x in readFDs:
            print 'read key : '+ str(x) + ' baseport : '+str(servSock[x].baseport)
        for x in writeFDs:
            print 'write key : '+ str(x) + ' baseport : '+str(servSock[x].baseport)
    # map read socket fds to read socket names in a dictionary
    # assuming we have servSock[]

    while 1:
        start = time.time()
        
        rReady, wReady, eReady = select.select(readFDs, writeFDs, exceptFDs, 20)

        # timeout handling
        if len(rReady) == 0:
            print "Timeout Error: No available sockets"
        # read available messages
        else:
            for fd in rReady:
                # read all data in socket and parse messages
                data = readAll(servSock[fd][0])
                messages = msgSplit(data)
                for m in messages:
                    DVUpdateMessage(servSock[fd][1], m)
        # send updated DVtable to all available neighbors
        for fd in wReady:
            servSock[fd][0].send(data)
        
        FD_ZERO(rReady)
        FD_ZERO(wReady)
        FD_ZERO(eReady)
        end = time.time()

        # updates sent every 30 seconds
        t = 30 - end + start
        if t >= 0 and t < 30: time.sleep(t)



def makelisten(host, port):
    print '----ENTERING MAKELISTEN Script-----'
    print 'host: ' + host

    print 'port: ' + str(port)

    try:
        #create an AF_INET, STREAM socket (TCP)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error, msg:
        print 'Failed to create socket. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
        sys.exit();
     
    print 'Socket Created'

    try:
        s.bind((host,port))
    except socket.error , msg:
        print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()
         
    print 'Socket bind complete'
    s.listen(10)
    print 'Socket now listening'
    return s

    #not sure what else to do as we didn't know how to listen or talk ect...

def makesend(host, port):
    bytes = random._urandom(1024)
    print '----ENTERING MAKESEND Script-----'
    print 'host: ' + host
    print 'port: ' + str(port)
    try:
        #create an AF_INET, STREAM socket (TCP)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error, msg:
        print 'Failed to create socket. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
        sys.exit();
     
    print 'Socket Created'
    try:
        s.bind((host,port))
    except socket.error , msg:
        print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()
         
    print 'Socket bind complete'

    return s



def readlinks(testname, router):
    f = open(testname+'/'+router+'.cfg')
    lines = f.readlines()
    table = {}
    for line in lines:
        if line[0]=='#': continue
        words = string.split(line)
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



def setupscript(testdirname,routername, poption):
    print '----ENTERING Set-Up Script-----'
    table = {}
    table = readrouters(testdirname)
    #for r in table:
        #print table['A']
    dvsimulator(poption,testdirname,routername)







dvsimulator(sys.argv)
    