import serial
import subprocess
import os
import numpy as np
import pdb
import time
ser = serial.Serial('/dev/tty.usbmodem1421', 9600, timeout=1)
print('Initialized')


def getDat():
	'''dat=str(ser.read(ser.inWaiting()))
	datList=dat.split('\\r\\n')
	done=False
	ind=-2
	while lastLine=='':
		ind-=1
		if ind< -20:
			print("WARNING: 20 reads")
		lastLine=datList[ind]
	'''
	dat=ser.readline()
	dat=dat.split() #split to list
	dat=np.asarray(list(map(int,dat))) #string list to int list
	if len(dat)>0:
		button=[dat[-1]]
		dat=dat[:-1]
		return dat, button

while True:
	try:
		dat, button = getDat()
		print(dat.tolist()+button)
	except:
		continue