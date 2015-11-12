import string
import socket
import sys
class RouterInfo:
    def __init__(self, host, baseport):
        self.host, self.baseport = host, baseport;

class LinkInfo:
    def __init__(self, cost, locallink, remotelink):
        self.cost, self.locallink, self.remotelink = cost, locallink, remotelink;
        
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
    for x in table:
        print "router info: "
        attrs = vars(table[x])
        print ', '.join("%s: %s" % item for item in attrs.items())
             
    return table
def dvsimulator(poption, testdirame, routerame, table):
    dvtable = {}
    print '----ENTERING dvsimulator-----'
    print "poption : "+ poption
    print "testdirame : "+ testdirame
    print "routerame : "+ routerame


    for x in table:
        print x
        attrs = vars(table[x])
        print 'baseport:'
        print attrs['baseport']
        #putting readlink table to the dv table
        dvtable[x[0]] = readlinks(testdirame, x[0])
        #creating output file
        f = open(x[0] + ".output",'w')
        f.close()

        makelisten(routerame,attrs['baseport'])
        for q in dvtable:
            print dvtable[q[0]]
            #I ENDED HERE!


        #attrs = vars(table[x])
        #print ', '.join("%s: %s" % item for item in attrs.items())

def makelisten(host, port):
    print '----ENTERING MAKELISTEN Script-----'
    print 'host:'
    print host
    print 'port'
    print port
    try:
        #create an AF_INET, STREAM socket (TCP)
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    except socket.error, msg:
        print 'Failed to create socket. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
        sys.exit();
     
    print 'Socket Created'

    try:
        s.bind(("127.0.0.1",port))
    except socket.error , msg:
        print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + msg[1]
        sys.exit()
         
    print 'Socket bind complete'
    s.listen(10)
    print 'Socket now listening'

    #not sure what else to do as we didn't know how to listen or talk ect...

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
    


def setupscript(testdirname, poption):
    print '----ENTERING Set-Up Script-----'
    table = {}
    table = readrouters(testdirname)
    for r in table:
        #print table['A']
        dvsimulator(poption,testdirname,r[0], table)


readrouters('test1')
#dvsimulator('hey','hey','hey')
setupscript('test1', '-d');

