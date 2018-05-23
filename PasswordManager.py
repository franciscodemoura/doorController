from datetime import datetime

class PasswordManager():
	def __init__(self, filename, group_messenger, replyer, conversations, null_date_symbol, date_string_format, date_readable_format):
		self.__filename             = filename
		self.__group_messenger      = group_messenger
		self.__conversations        = conversations
		self.__replyer              = replyer
		self.__null_date_symbol     = null_date_symbol
		self.__date_string_format   = date_string_format
		self.__date_readable_format = date_readable_format
		self.__loadPasswords()

	def __loadPasswords(self):
		self.__passwords = {}
		try:
			with open(self.__filename,'r') as file:
				for line in file:
					pieces = line[0:-1].split(' ')
					self.__passwords[pieces[0]] = (pieces[1], pieces[2])
		except:
			pass
		self.__savePasswords()

	def __savePasswords(self):
		self.__cleanPasswords()
		with open(self.__filename,'w') as file:
			for password in self.__passwords:
				file.write(password + ' ' + self.__passwords[password][0] + ' ' + self.__passwords[password][1] + '\n')
		
	def __cleanPasswords(self):
		continue_cleaning = True
		while continue_cleaning:
			continue_cleaning = False
			for password in self.__passwords:
				if self.__expired(password):
					del self.__passwords[password]
					self.__group_messenger(self.__conversations['password_expired_message'].format(password=password))
					continue_cleaning = True
					break
	
	def __expired(self, password):
		expiration_time = self.__passwords[password][1]
		if expiration_time == self.__null_date_symbol:
			return False
		return datetime.strptime(expiration_time, self.__date_string_format) <= datetime.now()
		
	def getFilename(self):
		return self.__filename
		
	def __enabled(self, password):
		enabling_time = self.__passwords[password][0]
		if enabling_time == self.__null_date_symbol:
			return True
		return datetime.strptime(enabling_time, self.__date_string_format) <= datetime.now()
	
	def removePassword(self, password):
		if self.__passwords.has_key(password):
			del self.__passwords[password]
			self.__savePasswords()
			return True
		else:
			return False
			
	def printPasswordBook(self):
		print(self.__passwords)
		
	def validatePassword(self, password):
		if self.__passwords.has_key(password):
			valid = self.__enabled(password) and not self.__expired(password)
			if not valid:
				self.__cleanPasswords()
			return valid
		else:
			return False

	def __validateDateTime(self, date_time):
		if date_time == self.__null_date_symbol:
			return (True, )
		try:
			dt = datetime.strptime(date_time, self.__date_string_format)
			return (True, dt)
		except ValueError:
			return (False, )

	def registerPassword(self, password, from_time, to_time):
		from_time = from_time.upper()
		to_time = to_time.upper()

		from_time_converted = self.__validateDateTime(from_time)
		to_time_converted = self.__validateDateTime(to_time)

		if not from_time_converted[0]:
			return (False, self.__conversations['ill_formed_date_message'].format(date=from_time,null_symbol=self.__null_date_symbol,date_format=self.__date_readable_format))
		if not to_time_converted[0]:
			return (False, self.__conversations['ill_formed_date_message'].format(date=to_time,null_symbol=self.__null_date_symbol,date_format=self.__date_readable_format))

		if from_time != self.__null_date_symbol:
			if from_time_converted[1] <= datetime.now():
				return (False, self.__conversations['enable_date_past_message'])
		if to_time != self.__null_date_symbol:
			if to_time_converted[1] <= datetime.now():
				return (False, self.__conversations['expiration_date_past_message'])
		if from_time != self.__null_date_symbol and to_time != self.__null_date_symbol:
			if from_time_converted[1] >= to_time_converted[1]:
				return (False, self.__conversations['invalid_date_interval_message'])

		self.removePassword(password)
		self.__passwords[password] = (from_time, to_time)
		self.__savePasswords()

		return (True, '')

	def replyWithPasswords(self, message):
		self.__cleanPasswords()
		if len(self.__passwords) == 0:
			self.__replyer(message, self.__conversations['no_registered_password_message'])
		else:
			for password in self.__passwords:
				self.__replyer(message, password + ' ' + self.__passwords[password][0] + ' ' + self.__passwords[password][1])

	def removeAllPasswords(self):
		self.__passwords = {}
		self.__savePasswords()

