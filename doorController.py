#!/usr/bin/python
# -*- coding: utf-8 -*-

from telegram.ext            import Updater, CommandHandler, MessageHandler, Filters
from datetime                import datetime
from PasswordManager         import PasswordManager
from BroadcastClientsManager import BroadcastClientsManager
from configuration           import doorStateMachine
from configuration           import commandPermissions
import requests
import RPi.GPIO as GPIO
import time

binaryToUpDown               = ['DOWN','UP']

doorState                    = '' #'CLOSED', OPEN, CLOSING, OPENING
lastTimeDoorClosed           = datetime.utcnow()
keepRunning                  = True
openDangerMessageSent        = True
openKeyState                 = 0
closedKeyState               = 0
userPasswords                = {}


def loadParameters():
	global conversations
	global commandNames

	conversations = readDictionaryFromFile('conversations.txt')
	parameters    = readDictionaryFromFile('parameters.txt')
	commandNames  = readDictionaryFromFile('commands.txt')

	global botToken
	global doorGroupURL
	global chatId
	global meetingPhrase
	global allPasswordsCommandParameter
	global dateStringFormat
	global dateReadableFormat
	global nullDateSymbol
	global closedKeyChannel
	global openKeyChannel
	global buttonKeyChannel
	global buttonPressingTime
	global maximumOpenTime
	global broadcastRegisterTime
	global adminIds
	global invertKeyChannels

	botToken                     =         parameters[ 'botToken'                     ]
	doorGroupURL                 =         parameters[ 'doorGroupURL'                 ]
	chatId                       =         parameters[ 'chatId'                       ]
	meetingPhrase                =         parameters[ 'meetingPhrase'                ]
	allPasswordsCommandParameter =         parameters[ 'allPasswordsCommandParameter' ]
	dateStringFormat             =         parameters[ 'dateStringFormat'             ]
	dateReadableFormat           =         parameters[ 'dateReadableFormat'           ]
	nullDateSymbol               =         parameters[ 'nullDateSymbol'               ]
	closedKeyChannel             = int   ( parameters[ 'closedKeyChannel'             ] )
	openKeyChannel               = int   ( parameters[ 'openKeyChannel'               ] )
	buttonKeyChannel             = int   ( parameters[ 'buttonKeyChannel'             ] )
	buttonPressingTime           = float ( parameters[ 'buttonPressingTime'           ] )
	maximumOpenTime              = int   ( parameters[ 'maximumOpenTime'              ] )
	broadcastRegisterTime        = int   ( parameters[ 'broadcastRegisterTime'        ] )
	adminIds                     =         parameters[ 'adminIds'                     ].split(',')
	invertKeyChannels            =         parameters[ 'invertKeyChannels'            ] == 'True'


def sendMessageToDoorGroup(message):
	try:
		r = requests.post(\
			doorGroupURL,\
			data = {\
				'chat_id':chatId,\
				'text':message\
				}\
			)
		return '200' in str(r)

	except:
		return False;


def sendMessageToRegisteredClients(message):
	broadcastClientsManager.broadcastMessage(message)


def registerForBroadcast(message):
	user_id = str(message.from_user.id)
	broadcastClientsManager.insertClient(user_id,message.reply_text)


def broadcastMessage(message):
	sendMessageToDoorGroup(message)
	sendMessageToRegisteredClients(message)


def readDictionaryFromFile(filename):
	dictionary = {}
	try:
		with open(filename,'r') as file:
			for line in file:
				pieces = line[0:-1].split('=')
				dictionary[pieces[0].strip()] = pieces[1].strip()
		return dictionary
	except:
		return {}


def replyText(message, text):
	try:
		message.reply_text(text)
	except:
		pass
		

def getHumanReadableDoorState(state):
	states = {\
		'CLOSED'  : conversations[ 'closed_state_name'  ] ,\
		'OPEN'    : conversations[ 'open_state_name'    ] ,\
		'CLOSING' : conversations[ 'closing_state_name' ] ,\
		'OPENING' : conversations[ 'opening_state_name' ]  \
		}
	return states[state]


def getActorName(user):
	return\
		user.first_name +\
		' (' +\
			'last_name = ' + user.last_name + \
			', id = '      + str(user.id) + \
		')'


def nextState(state, key_transition, other_key):
	return doorStateMachine[ (state, key_transition, other_key) ]
	

def readCommandPieces(command_line):
	return command_line.split(' ')
		

def setUserPassword(user_id, password):
	global userPasswords
	if userPasswords.has_key(user_id):
		del userPasswords[user_id]
	if passwordManager.validatePassword(password):
		userPasswords[user_id] = password
		return True;
	return False


def getUserPassword(user_id):
	global userPasswords
	if userPasswords.has_key(user_id):
		password = userPasswords[user_id]
		if passwordManager.validatePassword(password):
			return password
		else:
			del userPasswords[user_id]
	return ''


def validateUserAndParameters(message, command, parameters):
	if not commandPermissions.has_key(command):
		return (False, conversations['invalid_command_message'], [])

	(admin_can, user_can, password_needed) = commandPermissions[command]
	user_id = str(message.from_user.id)
	
	is_admin = False
	for id in adminIds:
		if user_id == id:
			is_admin = True
			break
		
	if not(is_admin and admin_can or not is_admin and user_can):
		return (False, conversations['access_denied_to_user_message'], [])

	needed_command_pieces = 1
	if not is_admin and password_needed:
		needed_command_pieces += 1
	needed_command_pieces += parameters

	command_pieces = readCommandPieces(message.text)
	number_of_given_pieces = len(command_pieces)

	if not is_admin and password_needed:
		if number_of_given_pieces == needed_command_pieces:
			setUserPassword(user_id, command_pieces[1])
		elif number_of_given_pieces + 1 == needed_command_pieces:
			user_password = getUserPassword(user_id)
			if user_password <> '':
				number_of_given_pieces += 1
				command_pieces.insert(1, user_password)

	if number_of_given_pieces <> needed_command_pieces:
		if number_of_given_pieces < needed_command_pieces:
			return (False, conversations['wrong_number_of_pars_message_passwd'], [])
		else:
			return (False, conversations['wrong_number_of_pars_message'], [])

	if not(is_admin or not password_needed):
		attempt = command_pieces[1]
		valid_password = passwordManager.validatePassword(attempt)
		if not valid_password:
			return (False, conversations['invalid_password_message'], [])
	
	if is_admin or not password_needed:
		return (True, '', command_pieces[1:])
	else:
		return (True, '', command_pieces[2:])


def checkCommand(update, command_name, action_description, parameters):
	(valid, error_message, split_parameters) = validateUserAndParameters(update.message, command_name, parameters)
	if valid:
		return (True, split_parameters)
	else:
		replyText(update.message, error_message)
		sendMessageToDoorGroup(conversations['action_failed_message'].format(actor=getActorName(update.message.from_user),action=action_description))
		return (False, [])
		

def start_command_callback(bot, update):
	(valid, parameters) = checkCommand(update, 'start', conversations['start_action_description'], 0)
	if not valid:
		return
	replyText(update.message, conversations['hello_message'].format(meeting_phrase=meetingPhrase))
	registerForBroadcast(update.message)


def open_command_callback(bot, update):
	(valid, parameters) = checkCommand(update, 'open', conversations['open_action_description'], 0)
	if not valid:
		return

	if doorState == 'CLOSED':
		pressButton()
		replyText(update.message, conversations['open_command_reply_message'])
		registerForBroadcast(update.message)
		sendMessageToDoorGroup(conversations['group_opening_message'].format(actor=getActorName(update.message.from_user)))
	else:
		replyText(update.message, conversations['no_action_reply_message'].format(state=getHumanReadableDoorState(doorState)))
		registerForBroadcast(update.message)


def close_command_callback(bot, update):
	(valid, parameters) = checkCommand(update, 'close', conversations['close_action_description'], 0)
	if not valid:
		return

	if doorState == 'OPEN':
		pressButton()
		replyText(update.message, conversations['close_command_reply_message'])
		registerForBroadcast(update.message)
		sendMessageToDoorGroup(conversations['group_closing_message'].format(actor=getActorName(update.message.from_user)))
	else:
		replyText(update.message, conversations['no_action_reply_message'].format(state=getHumanReadableDoorState(doorState)))
		registerForBroadcast(update.message)


def activate_command_callback(bot, update):
	(valid, parameters) = checkCommand(update, 'activate', conversations['activate_action_description'], 0)
	if not valid:
		return
	pressButton()
	replyText(update.message, conversations['activation_command_reply_message'])
	registerForBroadcast(update.message)
	sendMessageToDoorGroup(conversations['group_activation_message'].format(actor=getActorName(update.message.from_user)))


def status_command_callback(bot, update):
	(valid, parameters) = checkCommand(update, 'status', conversations['status_action_description'], 0)
	if not valid:
		return
	replyText(update.message, conversations['situation_command_reply_message'].format(state=getHumanReadableDoorState(doorState)))
	registerForBroadcast(update.message)
    	

def stop_command_callback(bot, update):
	(valid, parameters) = checkCommand(update, 'stop', conversations['stop_action_description'], 0)
	if not valid:
		return
	global keepRunning
	keepRunning = False
	replyText(update.message, conversations['stop_command_reply_message'])
	registerForBroadcast(update.message)
	sendMessageToDoorGroup(conversations['group_stopping_message'].format(actor=getActorName(update.message.from_user)))


def def_password_command_callback(bot, update):
	(valid, parameters) = checkCommand(update, 'def_password', conversations['set_password_action_description'], 3)
	if not valid:
		return

	if parameters[1] == '-' and parameters[2] == '-':
		if parameters[0] == '-':
			passwordManager.removeAllPasswords()
			replyText(update.message, conversations['all_passwords_removed_message'])
			registerForBroadcast(update.message)
		else:
			if passwordManager.removePassword(parameters[0]):
				replyText(update.message, conversations['password_removed_message'])
				registerForBroadcast(update.message)
			else:
				replyText(update.message, conversations['invalid_or_expired_password_message'])
				registerForBroadcast(update.message)
		return

	(valid, error_message) = passwordManager.registerPassword(parameters[0], parameters[1], parameters[2])

	if not valid:
		replyText(update.message, error_message)
		registerForBroadcast(update.message)
	else:
		replyText(update.message, conversations['password_registered_message'].format(password=parameters[0]))
		registerForBroadcast(update.message)


def password_ck_command_callback(bot, update):
	(valid, parameters) = checkCommand(update, 'password_ck', conversations['check_password_action_description'], 1)
	if not valid:
		return

	password = parameters[0]

	if password == allPasswordsCommandParameter:
		passwordManager.replyWithPasswords(update.message)
	else:
		valid = passwordManager.validatePassword(password)
		if valid:
			replyText(update.message, conversations['valid_password_message'])
			registerForBroadcast(update.message)
		else:
			replyText(update.message, conversations['invalid_or_expired_password_message'])
			registerForBroadcast(update.message)


def put_password_command_callback(bot, update):
	(valid, parameters) = checkCommand(update, 'put_password', conversations['put_password_action_description'], 1)
	if not valid:
		return

	if setUserPassword(str(update.message.from_user.id), parameters[0]):
		replyText(update.message, conversations['valid_and_used_password_message'])
		registerForBroadcast(update.message)
	else:
		replyText(update.message, conversations['invalid_or_expired_password_message'])
			

def diagnosis_command_callback(bot, update):
	(valid, parameters) = checkCommand(update, 'diagnosis', conversations['diagnosis_action_description'], 0)
	if not valid:
		return

	replyText( update.message, 'doorState = '                    + str( doorState                    ) )
	replyText( update.message, 'lastTimeDoorClosed = '           + str( lastTimeDoorClosed           ) )
	replyText( update.message, 'openDangerMessageSent = '        + str( openDangerMessageSent        ) )
	replyText( update.message, 'openKeyState = '                 + str( openKeyState                 ) )
	replyText( update.message, 'closedKeyState = '               + str( closedKeyState               ) )
	replyText( update.message, 'userPasswords = '                + str( userPasswords                ) )
	replyText( update.message, 'nullDateSymbol = '               + str( nullDateSymbol               ) )
	replyText( update.message, 'maximumOpenTime = '              + str( maximumOpenTime              ) )
	replyText( update.message, 'adminIds = '                     + str( adminIds                     ) )
	replyText( update.message, 'dateStringFormat = '             + str( dateStringFormat             ) )
	replyText( update.message, 'dateReadableFormat = '           + str( dateReadableFormat           ) )
	replyText( update.message, 'buttonPressingTime = '           + str( buttonPressingTime           ) )
	replyText( update.message, 'invertKeyChannels = '            + str( invertKeyChannels            ) )
	replyText( update.message, 'allPasswordsCommandParameter = ' + str( allPasswordsCommandParameter ) )
	registerForBroadcast(update.message)


def unknown_command(bot, update):
	replyText( update.message, conversations['unknown_command_message'])


def defineCallbacks(updater):
	updater.dispatcher.add_handler( CommandHandler( commandNames[ 'start'        ] , start_command_callback        ) )
	updater.dispatcher.add_handler( CommandHandler( commandNames[ 'open'         ] , open_command_callback         ) )
	updater.dispatcher.add_handler( CommandHandler( commandNames[ 'close'        ] , close_command_callback        ) )
	updater.dispatcher.add_handler( CommandHandler( commandNames[ 'activate'     ] , activate_command_callback     ) )
	updater.dispatcher.add_handler( CommandHandler( commandNames[ 'status'       ] , status_command_callback       ) )
	updater.dispatcher.add_handler( CommandHandler( commandNames[ 'stop'         ] , stop_command_callback         ) )
	updater.dispatcher.add_handler( CommandHandler( commandNames[ 'def_password' ] , def_password_command_callback ) )
	updater.dispatcher.add_handler( CommandHandler( commandNames[ 'password_ck'  ] , password_ck_command_callback  ) )
	updater.dispatcher.add_handler( CommandHandler( commandNames[ 'put_password' ] , put_password_command_callback ) )
	updater.dispatcher.add_handler( CommandHandler( commandNames[ 'diagnosis'    ] , diagnosis_command_callback    ) )
	updater.dispatcher.add_handler( MessageHandler( Filters.command                , unknown_command               ) )


def createUpdater():
	return Updater(botToken)


def initGPIO():
	GPIO.cleanup()
	GPIO.setmode(GPIO.BCM)
	GPIO.setup( closedKeyChannel , GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup( openKeyChannel   , GPIO.IN, pull_up_down=GPIO.PUD_UP)
	GPIO.setup( buttonKeyChannel , GPIO.OUT                         )
	

def finalizeGPIO():
	GPIO.cleanup()


def pressButton():
	GPIO.output(buttonKeyChannel,GPIO.HIGH)
	time.sleep(buttonPressingTime)
	GPIO.output(buttonKeyChannel,GPIO.LOW)


def readChannel(channel):
	if invertKeyChannels:
		return 1 - GPIO.input(channel)
	else:
		return GPIO.input(channel)


def initializeGPIOEventDetection():
	GPIO.add_event_detect( closedKeyChannel, GPIO.BOTH, closedKeyCallback )
	GPIO.add_event_detect( openKeyChannel  , GPIO.BOTH, openKeyCallback   )


def initializeDoorState():
	global openKeyState
	global closedKeyState
	openKeyState   = readChannel(openKeyChannel)
	closedKeyState = readChannel(closedKeyChannel)
	if closedKeyState == 1:
		return 'CLOSED'
	else:
		return 'OPEN'


def updateDoorState():
	global openKeyState
	global closedKeyState
	global doorState

	openKeyPreviousState   = openKeyState
	closedKeyPreviousState = closedKeyState

	openKeyState   = readChannel(openKeyChannel)
	closedKeyState = readChannel(closedKeyChannel)
	
	global doorState
	previousState = doorState

	if openKeyState != openKeyPreviousState:
		if openKeyState == 1:
			(doorState, error, message) = nextState(doorState, 'OPEN_KEY_UP', binaryToUpDown[closedKeyState])
			if error:
				sendMessageToDoorGroup('State error! Current=' + previousState + ', key transition=' + 'OPEN_KEY_UP' + ', other key=' + binaryToUpDown[closedKeyState])
		else:
			(doorState, error, message) = nextState(doorState, 'OPEN_KEY_DOWN', binaryToUpDown[closedKeyState])
			if error:
				sendMessageToDoorGroup('State error! Current=' + previousState + ', key transition=' + 'OPEN_KEY_DOWN' + ', other key=' + binaryToUpDown[closedKeyState])
		if message != '':
			broadcastMessage(conversations[message])

	if closedKeyState != closedKeyPreviousState:
		if closedKeyState == 1:
			(doorState, error, message) = nextState(doorState, 'CLOSED_KEY_UP', binaryToUpDown[openKeyState])
			if error:
				sendMessageToDoorGroup('State error! Current=' + previousState + ', key transition=' + 'CLOSED_KEY_UP' + ', other key=' + binaryToUpDown[openKeyState])
		else:
			(doorState, error, message) = nextState(doorState, 'CLOSED_KEY_DOWN', binaryToUpDown[openKeyState])
			if error:
				sendMessageToDoorGroup('State error! Current=' + previousState + ', key transition=' + 'CLOSED_KEY_DOWN' + ', other key=' + binaryToUpDown[openKeyState])
		if message != '':
			broadcastMessage(conversations[message])
	
	global lastTimeDoorClosed
	global openDangerMessageSent

	if closedKeyState == 1:
		lastTimeDoorClosed = datetime.utcnow()
		openDangerMessageSent = False
	else:
		if (datetime.utcnow() - lastTimeDoorClosed).total_seconds() > maximumOpenTime:
			if not openDangerMessageSent:
				broadcastMessage(conversations['door_open_timeout_message'].format(seconds=str(maximumOpenTime)))
				openDangerMessageSent = True


def sendStartMessage():
	count = 0
	while not sendMessageToDoorGroup(conversations['group_starting_message']) and count < 10:
		time.sleep(3.0)
		count += 1
		

def openKeyCallback(channel):
	updateDoorState()


def closedKeyCallback(channel):
	updateDoorState()



loadParameters()

sendStartMessage()

passwordManager = PasswordManager('passwords.txt', sendMessageToDoorGroup, replyText, conversations, nullDateSymbol, dateStringFormat, dateReadableFormat)
broadcastClientsManager = BroadcastClientsManager(broadcastRegisterTime)
		
updater = createUpdater()
defineCallbacks(updater)
updater.start_polling(clean=True)

initGPIO()
doorState = initializeDoorState()

if doorState != 'CLOSED':
	sendMessageToDoorGroup(conversations['open_at_initialization_message'])

initializeGPIOEventDetection()

while keepRunning:
	time.sleep(1.0)
	updateDoorState()
else:
	updater.stop()
	finalizeGPIO()
