import string
import socket
import sys
import random
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
    


def setupscript(testdirname,routername, poption):
    print '----ENTERING Set-Up Script-----'
    table = {}
    table = readrouters(testdirname)
    #for r in table:
        #print table['A']
    dvsimulator(poption,testdirname,routername)


#readrouters('test1')
#dvsimulator('hey','hey','hey')
if __name__ == "__main__":
	setupscript(sys.argv[1], sys.argv[2],sys.argv[3] );

