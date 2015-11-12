import string
class RouterInfo:
    def __init__(self, host, baseport):
        self.host, self.baseport = host, baseport;

class LinkInfo:
    def __init__(self, cost, locallink, remotelink):
        self.cost, self.locallink, self.remotelink = cost, locallink, remotelink
#everything is global till we create more of an outline

RouterTable = {}

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
    TestList = [TestUMessageNoChange,TestUMessageIncrease, TestUMessageDecrease]
    for test in TestList:
        if(test()):
            passed = passed + 1
        total = total + 1
    print("DVUpdate: ", passed ," passed out of ", total)
    return passed, total

def TestUMessageNoChange():
    RouterTable.clear()
    RouterTable["A"] = LinkInfo(int(1), int(2), int(3))
    RouterTable["B"] = LinkInfo(int(2), int(2), int(3))
    DVUpdateMessage("U A 1 B 2")
    TestTable = {"A" : 1, "B" : 2}
    if(AssertRouterTable(TestTable)):
        print("TestUMessageNoChange Passed")
        return True
    else:
        print("TestUMessageNoChange Failed")
        return False
    
def TestUMessageIncrease():
    RouterTable.clear()
    RouterTable["A"] = LinkInfo(int(1), int(2), int(3))
    RouterTable["B"] = LinkInfo(int(2), int(2), int(3))
    DVUpdateMessage("U A 2 B 2")
    TestTable = {"A" : 2, "B" : 2}
    if(AssertRouterTable(TestTable)):
        print("TestUMessageIncrease Passed")
        return True
    else:
        print("TestUMessageIncrease Failed")
        return False

def TestUMessageDecrease():
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
    
def AssertRouterTable(TestTable):
    for entry in TestTable:
        if(RouterTable[entry].cost != TestTable[entry]):
            return False        
    return True

def DVUpdateMessage(Message):
    print(Message)

def SendUMessage():
    Message = "U"
    for entry in RouterTable:
        Message = Message + " " + entry + " " + RouterTable[entry].cost
    SendToAllNeighbor(Message)

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



