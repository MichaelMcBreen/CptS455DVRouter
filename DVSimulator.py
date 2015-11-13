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
    if(AssertRouterTable(TestTable)):
        print("TestUMessageNoChange Passed")
        return True
    else:
        print("TestUMessageNoChange Failed")
        return False
    
def TestUMessageNextHop():
    RouterTable.clear()
    RouterTable["A"] = {"A": 0,"B" : 64,"C": 64, "D": 64}
    RouterTable["B"] = {"A":64,"B" : 3,"C": 64, "D": 64}
    RouterTable["C"] = {"A":64,"B": 64,"C": 23, "D": 64}
    RouterTable["D"] = {"A":64,"B": 64, "C": 64, "D" : 64}
    DVUpdateMessage("B","U A 3 B 0 C 2 D 64")
    TestTable = {}
    TestTable["A"] = {"A": 0,"B" : 64,"C": 64, "D": 64}
    TestTable["B"] = {"A":64,"B" : 3,"C": 25, "D": 64}
    TestTable["C"] = {"A":64,"B": 5,"C": 23, "D": 64}
    TestTable["D"] = {"A":64,"B": 64, "C": 28, "D" : 64}
    PrintRoutingTable(RouterTable)
    if(AssertRouterTable(TestTable)):
        print("TestUMessageNextHop Passed")
        return True
    else:
        print("TestUMessageNextHop Failed")
        return False

def TestUMessageLastHop():
    RouterTable.clear()
    RouterTable["A"] = LinkInfo(int(1), int(2), int(3))
    RouterTable["B"] = LinkInfo(int(2), int(2), int(3))
    DVUpdateMessage("U A 1 B 1")
    
    TestTable = {"A" : 1, "B" : 1}
    if(AssertRouterTable(TestTable)):
        print("TestUMessageDecrease Passed")
        return True
    else:
        print("TestUMessageDecrease Failed")
        return False

def PrintRoutingTable(Table):
    ##prints top label for table
    print("from ", SelfName,": ", end="")
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


def SendUMessage():
    Message = "U"
    #build U Message from our routing table
    for entry in RouterList:
        Message = Message + " " + entry + " " + str(GetLowestCostForRouter(entry))
    print(Message)
    #SendToAllNeighbor(Message)

def SendToAllNeighbor(Message):
    for entry in RouterTable:
        SendToNeighBor(entry, Message)

def SendToNeighBor(NeighBor, Message):
    print("dfsdffdsf")
    #send message based the Neighbor field


#Sudo Code from the Book for Distance Vector Algorithm

#At Each Node,x:
#Initialization:
#   for all deestinations y in N:
#       Dx(y) = c(x,y) # if y is not a neighbor then c(x,y) = inf
#   for each neighbor w
#       Dw(y) = ? for all destinations y in N
#   for each nieghbor w
#       send distance Vector Dx = [Dx(y): y in N] to w
#loop
#   wait (until I see a link cost change to some neighbor w or
#           until I receive a distance vecotr from some neighbor w)
#   for each y in N:
#       Dx(y) = minv{x(x,y) + Dv(y)}
#   if(Dx(y)) change for any destination y
#       send distance vector Dx = [Dx(y): y in N] to all neighbors
#forever



