
import select
import string
import time

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


# assuming we have servSock[], maxDescPlus1, numSockets
while 1:
	start = time.time()
	rReady, wReady, eReady = select.select(readFDs, writeFDs, exceptFDs, 0);

	if len(rReady) < 0:
		print "Select Error: failed to select available sockets\n"	# error handling????
	elif len(rReady) == 0:
		print "Timeout Error: No available sockets"
	else:
		for fd in rReady:
			# do something with serSock[fd]
			data = servSock[fd].recv(2048)
			updaterouterDVtable(data)
	
	for fd in writeFDs:
		servSock[fd].send(data)
	
	end = time.time()
	time.sleep(30 - end + start)








