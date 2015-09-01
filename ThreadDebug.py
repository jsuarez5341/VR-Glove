import serial
import subprocess
import os
import numpy as np
import pdb
import time
import threading
ser = serial.Serial('/dev/tty.usbmodem1421', 9600, timeout=1)
print('Initialized')

def getDat():
	dat=ser.readline()
	dat=dat.split() #split to list
	dat=np.asarray(list(map(int,dat))) #string list to int list
	if len(dat)>0:
		button=[dat[-1]]
		dat=dat[:-1]
		return dat, button

globDat=0
globButton=0
def threadGetDat():
	global globDat
	global globButton
	dat=[0]
	button=0
	counter=0 #avoid difficult to debug errors
	while sum(dat)==0 and button==0:
		counter+=1
		try:
			dat, button=getDat()
			globDat=dat
			globButton=button
			#print("dat: "+str(dat)+", button: "+str(button))
		except:
			pdb.set_trace()
			if counter>100:
				print("Stuck in while loop")
	threading.Timer(.02, threadGetDat).start() #call self in .1 seconds
def pollDat():
	print("dat: "+str(globDat)+", button: "+str(globButton))
	threading.Timer(.02, pollDat).start() #call self in .1 seconds

threadGetDat()
pollDat()