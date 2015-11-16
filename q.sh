#!/bin/bash
routers[0] = "A"
routers[1] = "B"
routers[2] = "C"
routers[3] = "D"
routers[4] = "E"

for i in {0..5}
do
	echo "python router $1 $2 routers[i]"
	# pass -p testdir routername
	py router $2 $3 routers[i] 
done
