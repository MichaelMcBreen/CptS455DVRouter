import string

class RouterInfo:
    def __init__(self, host, baseport):
        self.host, self.baseport = host, baseport;

class LinkInfo:
    def __init__(self, cost, locallink, remotelink):
        self.cost, self.locallink, self.remotelink = cost, locallink, remotelink
#everything is global till we create more of an outline
RouterTable = {} #Dictionary of Dictionary
RouterList = ["A", "B", "C", "D"]
SelfName = "A"
PosionReverse = True
#used to run all tests
def Test():
    passed = 0
    total = 0
    passed, total = TestDVUpdate()
    print(passed, "/", total, " Test ran")

def TestDVUpdate():
    print("Running DVUpdate Tests")
    passed = 0
    total = 0
    TestList = [TestUMessageNoChange] #, TestUMessageNextHop]
    #TestList = [TestUMessageNoChange,TestUMessageIncrease, TestUMessageDecrease]
    for test in TestList:
        if(test()):
            passed = passed + 1
        total = total + 1
    print("DVUpdate: ", passed ," passed out of ", total)
    return passed, total

def TestUMessageNoChange():
    RouterTable.clear()
    RouterTable["A"] = {"A": 0,"B" : 64,"C": 64, "D": 64}
    RouterTable["B"] = {"A":64,"B" : 3,"C": 64, "D": 64}
    RouterTable["C"] = {"A":64,"B": 64,"C": 23, "D": 64}
    RouterTable["D"] = {"A":64,"B": 64, "C": 64, "D" : 64}
    DVUpdateMessage("B","U A 3 B 0 C 2 D 64")
    TestTable = {}
    TestTable["A"] = {"A": 0,"B" : 64,"C": 64, "D": 64}
    TestTable["B"] = {"A":64,"B" : 3,"C": 64, "D": 64}
    TestTable["C"] = {"A":64,"B": 64,"C": 23, "D": 64}
    TestTable["D"] = {"A":64,"B": 64, "C": 64, "D" : 64}
    DVUpdateMessage("C","U A 23 B 2 C 0 D 5")
    DVUpdateMessage("B","U A 3 B 0 C 2 D 7")
    DVUpdateMessage("C","U A 5 B 2 C 0 D 5")
    SendUMessage()
    ParseMessage("P")
    ParseMessage("P C")
    ParseMessage("L C 5")
    PrintRoutingTable(RouterTable)
    SendUMessage()
    if(AssertRouterTable(TestTable)):
        print("TestUMessageNoChange Passed")
        return True
    else:
        print("TestUMessageNoChange Failed")
        return False

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
        
        
#checks to see that each cell of the table matches
def AssertRouterTable(TestTable):
    for routerName in RouterList:
        for entry in RouterList:
            if(TestTable[routerName][entry] != RouterTable[routerName][entry]):
                return False
    return True

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
