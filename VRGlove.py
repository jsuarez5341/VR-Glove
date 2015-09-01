import serial
import subprocess
import os
import numpy as np
import pdb
import time
import threading
import tkinter
ser = serial.Serial('/dev/tty.usbmodem1421', 9600, timeout=1)
print('Initialized')

#--------------------

saveDat=np.load("saveDat.npy").tolist()

gloveState = 0#1 is inactive/edit command mode. 0 is active sensing
#[[336, 263, 329, 249]]
dbNames=saveDat["names"]
dbDescriptions=saveDat["descriptions"]
dbKeys=saveDat["keys"]
dbVals=saveDat["vals"]

gloveLow=saveDat["low"]
gloveHigh=saveDat["high"]

listLen=100
reqMax=3
nonMaxSupList=[None]*listLen

#--------------------

def makeCmd(keystr):
	cmd='''osascript<<END
	tell application "System Events"
		'''+str(keystr)+'''
	END
	'''
	return cmd

def getInput():
	return input(">>> ")

def clearSerial():
	ser.read(ser.inWaiting())
	time.sleep(.1)

def getDat():
	dat=ser.readline()
	dat=dat.split() #split to list
	dat=np.asarray(list(map(int,dat))) #string list to int list
	if len(dat)==5:
		button=[dat[-1]]
		dat=dat[:-1]
		return dat, button

def normalizeDat(dat):
	global gloveLow
	global gloveHigh
	dat=dat-gloveLow
	dat=dat/(gloveLow-gloveHigh)
	return dat

def undoNormalize(dat):
	global gloveLow
	global gloveHigh
	dat=dat*(gloveLow-gloveHigh)
	dat=dat+gloveLow
	return dat

globDat=0
globButton=0
def threadGetDat():
	global globDat
	global globButton
	global gloveLow
	global gloveHigh
	dat=[0]
	button=0
	counter=0 #avoid difficult to debug errors
	while sum(dat)==0 and button==0:
		counter+=1
		try:
			dat, button=getDat()
			dat=normalizeDat(dat)
			globDat=dat
			globButton=button
			#print("dat: "+str(dat)+", button: "+str(button))
		except:
			if counter>100:
				print("Stuck in while loop")
	threading.Timer(.02, threadGetDat).start() #call self in __ seconds
threadGetDat()


def pollDat():
	print("dat: "+str(globDat)+", button: "+str(globButton))
	threading.Timer(.02, pollDat).start() #call self in .1 seconds


def printMainUI():
	print('''
	CANCEL: Get out of this menu by typing "quit".

	Welcome to the Suarez VR Systems Configuration Page. Glove sensors deactivated.
	I will serve as your guide through this epic quest of customization.
	From this menu, you have FULL control over the number and type of gestures
	that your glove recognizes. You may enter the following:


	"help": Display detailed information regarding functionality of the glove.
	Essential for all new users. Also contains troubleshooting information.

	"save": Save current glove gestures. Gestures are loaded on glove boot.

	"config": Configure the glove. Recommended for all new users and if glove is buggy.

	"list": List all current gestures.

	"sensors": Mostly a dev tool. Shows sensor output (normalized).

	"new": Register a new gesture.

	"delete": Delete a previously registered gestures.

	"quit": Activate glove sensors and leave this menu. Or use the aluminum contacts.
	''')

def printHelp():
	print('''
	This section contains detailed information regarding usage and repair of your device.

	HARDWARE: The glove is controlled by an Arduino compatible Pro Micro chip
	running at 16MHz and 5V. Note that the micro USB port is fragile. The Pro
	Micro is connected to four 2.2in unidirectional flex sensors and a double 
	contact pad that functions as a button. The flex sensor circuits are 
	equipped with 10K resistors: shorting the flex sensor connections will not
	damage the the Pro Micro.

	SOFTWARE: Arduino code directly polls the glove sensors at 20Hz from the 
	Pro Micro. A Python 3.3.5 program computes gestures via a simple Euclidean 
	distance metric, controls active/inactive glove state, and operates this UI.
	AppleScript is embedded directly into the Python code and is responsible for
	emulating keystrokes.

	REPAIR: The flex sensors do occasionally fail. At time of writing, replacements
	can be purchased from SparkFun Electronics for $7.95 each. To replace a flex
	sensor, carefully undo the blue palm wrap tape and the tape securing the flex
	sensor to power and ground. Gently pull it from the plastic sheath and discard
	it. As the flex sensor pins are extremely short, the replacement sensor will
	require two soldered leads, as illustrated by the original. Note that they are 
	NOT bidirectional: replacements must be inserted with the striped portion facing
	up.
	''')

def hackPurge():
	for i in range(100):
		try:
			dat, button = getDat()
		except:
			continue

def loop():
	global gloveState
	global dbVals
	global dbKeys
	global dbNames
	global dbDescriptions
	global listLen
	global reqMax
	global nonMaxSupList
	global gloveLow
	global gloveHigh



	if globButton!=gloveState:
		#Swap states
		gloveState=globButton
		if globButton[0]==1:
			#Activate config edit mode/deactivate glove sense state
			printMainUI()

			donePrompt=False
			while not donePrompt:
				inp=getInput()

				#Input parsing routine
				if inp=="help":
					printHelp()
				elif inp=="new":
					print('''Enter a name for your gesture, or enter "cancel" to cancel.''')
					inp=getInput()
					if inp=="cancel" or inp=="rest":
						pass
					else:
						name=inp
						print('Name "'+name+'" registered. Enter a description for your gesture, or enter "cancel" to cancel.')
						inp=getInput()
						if inp=="cancel":
							pass
						else:
							description=inp;
							print('Description "'+description+'" registered. Enter a letter to bind (or the word right, left, up, down) or enter "cancel" to cancel.')
							inp=getInput()
							if inp=="cancel":
								pass
							else:
								key=inp
								if key=="left":
									key="key code 123"
								elif key=="right":
									key="key code 124"
								elif key=="down":
									key="key code 125"
								elif key=="up":
									key="key code 126"
								else:
									key='keystroke "'+str(key)+'"'

								print('Keystroke "'+key+'" registered. Make a gesture, press enter, then hold the gesture until you receive confirmation or enter "cancel" to cancel.')
								hackPurge()
								inp=getInput()
								time.sleep(1)

								dbNames+=[name]
								dbDescriptions+=[description]
								dbKeys+=[key]	
								dbVals+=[undoNormalize(globDat)]

								print('Gesture registered: '
								+ name+': "'+description+'" bound to keystroke: "'+key+'" with flex sensor positions: '+str(undoNormalize(globDat).tolist()))

				elif inp=="delete":
					print('Enter the name of a gesture to delete, or enter "cancel" to cancel.')
					inp=getInput()
					if inp=="cancel" or inp=="rest":
						pass
					else:
						name=inp
						indices=np.where(name==np.asarray(dbNames))
						if len(indices)<1:
							print('Invalid name: no such gesture')
						else:
							for ind in indices:
								dbNames.pop(ind)
								dbDescriptions.pop(ind)
								dbKeys.pop(ind)
								dbVals.pop(ind)
							print('Successfully removed gesture.')
				elif inp=="save":
					np.save("saveDat", {
						"names":dbNames,
						"descriptions":dbDescriptions,
						"keys":dbKeys,
						"vals":dbVals,
						"low":gloveLow,
						"high":gloveHigh
						})
				elif inp=="config":
					print("Extend your hand all the way, press enter, and hold the gesture until you receive confirmation")
					inp=getInput()
					gloveHigh=undoNormalize(globDat)
					print("Confirmed"+str(gloveHigh)+". Close hand (do NOT clench or sensors won't work), press enter, and hold the gesture until you receive confirmation")
					inp=getInput()
					gloveLow=undoNormalize(globDat)
					print("Confirmed"+str(gloveLow)+". Relax your hand to natural position, press enter, and hold the gesture until you receive confirmation")
					inp=getInput()
					rest=undoNormalize(globDat)
					dbVals[0]=rest
					print('Confirmed'+str(rest)+'. Run "save" to save this configuration.')
				elif inp=="list":
					for ind in range(len(dbNames)):
						print('NAME: '+dbNames[ind])
						print('DESCRIPTION: '+dbDescriptions[ind])
						print('KEY: '+str(dbKeys[ind]))
						print('VAL: '+str(dbVals[ind]))
						print(' ')
				elif inp=="sensors":
					print("Sensor mode activated for 10 seconds")
					time.sleep(1)
					for i in range(100):
						print(globDat+[globButton])
						time.sleep(.1)
					print("Sensor mode deactivated")

				elif inp=="quit":
					print("Sensors reactivated.")
					gloveState=0
					donePrompt=True
				else:
					print('''"'''+inp+'''"'''+'''is not a valid command. Valid commands are: "help" "save" "config" "list" "sensors" new" "delete" "quit" ''')

	if len(dbVals)>0:
		if sum(globDat)==0:
			print("Registering all 0. Shift glove position")
			pass #Error here
		normedDBVals=normalizeDat(dbVals)
		euclideanDists=np.sum((globDat-normedDBVals)**2, 1)
		minInd=np.argmin(euclideanDists)
		nonMaxSupList=nonMaxSupList[1:]+[minInd]
		#If all elements -reqmax: are equal to the last element and minInd!=0
		if np.sum(np.asarray(nonMaxSupList[-reqMax:])==nonMaxSupList[-1])==len(nonMaxSupList[-reqMax:]) and minInd!=0:
			nonMaxSupList=[None]*listLen #Reset list
			keystroke=dbKeys[minInd]
			cmd=makeCmd(keystroke)
			os.system(cmd)
			time.sleep(.15)
	threading.Timer(.05, loop).start() #call self in __ seconds
loop()

