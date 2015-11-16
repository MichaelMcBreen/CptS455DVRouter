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
        print ("router info: ")
        attrs = vars(table[x])
        print (', '.join("%s: %s" % item for item in attrs.items()))
             
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
    readFDs = []
    writeFDs = []
    toWriteFDs = []
    exceptFDs = []
    servSock =  {}
    rlTable = {}
    print ('calling readrouters(testDirName)')
    table = readrouters(testDirName)
    dvtable = {}
    print ('----ENTERING dvsimulator-----')
    print ("poption : "+ str(poption))
    print ("testDirName : "+ testDirName)
    print ("routerName : "+ routerName)
    #open up output file to log
    f = open(routerName + ".output", 'w')
    f.close()
    print ('------------------------------------------------------------------>hey')
    mybaseport = table.get(routerName).baseport
    print (table.get(routerName).baseport)
    #we should set up the baseport to listen
    servSock[table.get(routerName).baseport] = ServSockInfo((makelisten(table.get(routerName).host, table.get(routerName).baseport)), mybaseport)
    #making router listen on its baseport
    #servSock["q"] =ServSockInfo("9000",mybaseport)
    print ('------------------------------------------------------------------>baseport')
    print (servSock.get(mybaseport).socket)
    rlTable = readlinks(testDirName,routerName)

    for neighbor in rlTable:
        print ('neighbor[0] = '+neighbor[0])
        myreadfds = table.get(routerName).baseport + rlTable.get(neighbor[0]).locallink
        mywritefds = table.get(neighbor[0]).baseport + rlTable.get(neighbor[0]).remotelink
        print ('myreadfds: '+ str(mywritefds))
        #for each link in our read link table
            #make listen for our locallink
            #make socket for our outgoing link
        #save FDS into read FDs    
        #tell it to listen by on the offset
        print ('creating socket and bind with incoming port and set it to listen...')
        tempSocket = makelisten(table.get(routerName).host, myreadfds)
        servSock[tempSocket] = neighbor, "R"
        readFDs.append(tempSocket) 
        print ('successfully created socket for listening')  
        #save socket into servSock dict with FDS as key and socket and output FDs are stored

        #save outgoing fds into writeFDs
        #now creating outgoing sockets
        print ('creating socket and bind with outgoing port...')
        tempSocket, outCome = makesend(table.get(neighbor[0]).host, mywritefds)
        if(outCome == True):
            writeFDs.append(tempSocket)
            servSock[tempSocket]  = neighbor, "W"
        else:
            toWriteFDS.append((table.get(neighbor[0]).host, mywritefds, neighbor))
        print ('successfully return outgoing socket...')
    # map read socket fds to read socket names in a dictionary
    # assuming we have servSock[]

    while 1:
        start = time.time()
        print("Looping at time: ", start)
        print("printing reads")
        printFDList(readFDs, servSock)
        print("printing write")
        printFDList(writeFDs, servSock)
        
        rReady, wReady, eReady = select.select(readFDs, writeFDs, exceptFDs, 20)

        #try to connect to read sockets that we could not earlier
        print("Making write sockets again...")
        for trySocket in toWriteFDs:
            print(trySocket[0], trySocket[1], trySocket[2])
            tempSocket, outCome = makesend(trySocket[0], trySocket[1])
            if(outCome == True):
                print("worked")
                writeFDs.append(tempSocket)
                servSock[mywritefds]  = trySocket[2], "W"
                toWriteFDs.remove(trySocket)
        
        # timeout handling
        if len(rReady) == 0:
            print ("Timeout Error: No available sockets")
        # read available messages
        else:
            for s in rReady:
                # read all data in socket and parse messages
                data = readAll(s)
                messages = msgSplit(data)
                for m in messages:
                    DVUpdateMessage(servSock[s], m)
        # send updated DVtable to all available neighbors
        for s in wReady:
            # needs to modify for poison and specific messages
            data = BuildUMessage()
            s.send(data)
        
        FD_ZERO(rReady)
        FD_ZERO(wReady)
        FD_ZERO(eReady)
        end = time.time()

        # updates sent every 30 seconds
        t = 30 - end + start
        if t >= 0 and t < 30: time.sleep(t)

def makelisten(host, port):
    print ('----ENTERING MAKELISTEN Script-----')
    print ('host: ' + host)

    print ('port: ' + str(port))

    try:
        #create an AF_INET, STREAM socket (TCP)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print ('Failed to create socket. Error code:')
        #sys.exit();
     
    print ('Socket Created')
    try:
        s.bind((host,port))
    except socket.error:
        print ('Bind failed. Error Code :1', socket.error)
        #sys.exit()
         
    print ('Socket bind complete')
    s.listen(10)
    print ('Socket now listening')
    return s

    #not sure what else to do as we didn't know how to listen or talk ect...

""" original code
def connect_all():

    print("enter connectALL")

    while unconnected_inputs or unconnected_outputs:

        for i in unconnected_outports:
            try:
                outputs[i].connect(address_out[i])
                print("connecect", i)
                unconnected_outputs.remove(i)
            expect socket.error:
                pass

        readable, writeable, exoectional = select.select(inputs.values(), outputs.values, inputs.values())

        for s in readable:
            for i in unconeected_inputs:
                if s in in inputs[s]:
                    inputs[i], adrl = s.acept()
                    print accpeted
                    unconnected_inputs.remove(i)
"""

def connect_all(servSock, connections, readS, writeS, toRead, toWrite):
    print("enter connectALL")
    while toRead or toWrite:

        for s in toWrite:
            try:
                s.connect(servSock.host, servSock.port)
                print("write connected", servSock.port)
                toWrite.remove(s)
            expect socket.error:
                pass
        rReady, wReady, eReady = select.select(readS, writeS, [])
        for s in rReady:
            for i in toRead:
                if s is in readS:
                    s.accept()
                    conn, sock = s.accept()
                    print("read connected", servSock.port)
                    toRead.remove(i)
                    connections.append(conn)


def create_connections():
    #initalize address_in/out, unconnected inputs/ output dictionaries

    #create outputs as a dict of name L 


def printFDList(socketDict, servSock):
    print("printing sockets")
    for entry in socketDict:
        print(entry, servSock[entry])

def makesend(host, port):
    print ('----ENTERING MAKESEND Script-----')
    print ('host: ' + host)
    print ('port: ' + str(port))
    try:
        #create an AF_INET, STREAM socket (TCP)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error:
        print ('Failed to create socket. Error code:')
        return s, False
     
    print ('Socket Created')
    try:
        s.bind((host,port))
    except socket.error:
        print("ERROR would not bind")
       return s, False
         
    print ('Socket bind complete')

    return s, True



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
    
