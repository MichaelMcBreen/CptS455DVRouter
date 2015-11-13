
import select
import string
import time
import re

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

# map read socket fds to read socket names in a dictionary
# assuming we have servSock[]

while 1:
	start = time.time()
	
	rReady, wReady, eReady = select.select(readFDs, writeFDs, exceptFDs, 0);

	# error handling
	if len(rReady) < 0:
		print "Select Error: failed to select available sockets\n"	# error handling????
	# timeout handling
	elif len(rReady) == 0:
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
	for fd in writeFDs:
		servSock[fd][0].send(data)
	
	end = time.time()
	# updates sent every 30 seconds
	time.sleep(30 - end + start)


