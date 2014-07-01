# PyTribe: classes to communicate with EyeTribe eye trackers
#
# author: Edwin Dalmaijer
# email: edwin.dalmaijer@psy.ox.ac.uk
# 
# version 1 (01-Jul-2014)


import json
import socket


class connection:
	
	"""class for connections with the EyeTribe tracker"""
	
	def __init__(self, host='localhost', port=6555):
		
		"""Initializes the connection with the EyeTribe tracker
		
		keyword arguments
		
		host		--	a string indicating the host IP, NOTE: currently only
					'localhost' is supported (default = 'localhost')
		port		--	an integer indicating the port number, NOTE: currently
					only 6555 is supported (default = 6555)
		"""
		
		# properties
		self.host = host
		self.port = port
		
		# initialize a connection
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((self.host,self.port))
	
	def request(self, category, request, values):
		
		"""Send a message over the connection
		
		arguments
		
		category	--	string indicating the query category
		request	--	string indicating the actual request of the message
		values	--	dict or list containing parameters of the request
		"""
		
		# create a JSON formatted string
		msg = self.create_json(category, request, values)
		# send the message over the connection
		response = self.sock.send(msg)
		# get response
		if type(response) != str:
			try:
				response = self.sock.recv(32768)
			except:
				self.revive()
				response = self.sock.recv(32768)
		# return the parsed response
		return self.parse_json(response)
	
	def create_json(self, category, request, values):
		
		"""Creates a new json message, in the format that is required by the
		EyeTribe tracker; these messages consist of a categort, a request and
		a (list of) value(s), which can be thought of as class.method.value
		(for more info, see: http://dev.theeyetribe.com/api/)
		
		arguments
		
		category	--	query category (string), e.g. 'tracker',
					'calibration', or 'heartbeat'
		request	--	the request message (string), e.g. 'get' for the
					'tracker' category
		values	--	a dict of parameters and their values, e.g.
					{"push":True, "version":1}
					OR:
					a list of parameters, e.g. ['push','iscalibrated']
					OR:
					None to pass no values at all
		
		keyword arguments
		
		None
		
		returns
		
		jsonmsg	--	a string in json format, that can be directly sent to
					the EyeTribe tracker
		"""
	
		# check if 'values' is a dict
		if type(values) == dict:
			# create a value string
			valuestring = '''{\n'''
			# loop through all keys of the value dict			
			for k in values.keys():
				# add key and value
				valuestring += '\t\t"%s": %s,\n' % (k, values[k])
			# omit final comma
			valuestring = valuestring[:-2]
			valuestring += '\n\t}'
		# check if 'values' is a tuple or a list
		elif type(values) in [list,tuple]:
			# create a value string
			valuestring = '''[ "'''
			# compose a string of all the values
			valuestring += '", "'.join(values)
			# append the list ending
			valuestring += '" ]'
		# check if there are no values
		elif values == None:
			pass
		# error if the values are anything other than a dict, tuple or list
		else:
			raise Exception("values should be dict, tuple or list, not '%s' (values = %s)" % (type(values),values))
		
		# create the json message
		if values == None:
			jsonmsg = '''
{
"category": "%s",
"request": "%s",
''' % (category, request)
		else:
			jsonmsg = '''
{
"category": "%s",
"request": "%s",
"values": %s
}''' % (category, request, valuestring)
		
		return jsonmsg

	def parse_json(self, jsonmsg):
		
		"""Parses a json message as those that are usually returned by the
		EyeTribe tracker
		(for more info, see: http://dev.theeyetribe.com/api/)
		
		arguments
		
		jsonmsg	--	a string in json format
		
		keyword arguments
		
		None
		
		returns
		
		msg		--	a dict containing the information in the json message;
					this dict has the following content:
						{	"category":	"tracker",
							"request":	"get",
							"statuscode":	200,
							"values":	{	"push":True,
										"iscalibrated":True
										}
							}
		"""
		
		# parse json message
		parsed = json.loads(jsonmsg)
		
		return parsed
	
	def revive(self):
		
		"""Re-establishes a connection
		"""
		
		# close old connection
		self.close()
		# initialize a connection
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sock.connect((self.host,self.port))

	
	def close(self):
		
		"""Closes the connection to the EyeTribe tracker
		"""
		
		# close the socket connection
		self.sock.close()


class tracker:
	
	"""class for SDK Tracker state and information related requests"""
	
	def __init__(self, connection):

		"""Initializes a tracker instance
		
		arguments
		
		connection	--	a pytribe.connection instance for the currently
						attached EyeTribe tracker
		"""
		
		self.connection = connection
		self.push = True
	
	def set_connection(self, connection):
		
		"""Set a new connection
		
		arguments
		
		connection	--	a pytribe.connection instance for the currently
						attached EyeTribe tracker
		"""
		
		self.connection = connection
	
	def get_push(self):
		
		"""Returns a Booleam reflecting the state: True for push mode,
		False for pull mode (Boolean)
		"""
		
		# send the request
		response = self.connection.request('tracker', 'get', ['push'])
		# return value or error
		if response['statuscode'] == 200:
			return response['values']['push'] == 'true'
		else:
			raise Exception("Error in tracker.get_push: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def get_heartbeatinterval(self):
		
		"""Returns the expected heartbeat interval in milliseconds
		(integer)
		"""
		
		# send the request
		response = self.connection.request('tracker', 'get', ['heartbeatinterval'])
		# check if the tracker is in push mode
		if response['statuscode'] == 200:
			return response['values']['heartbeatinterval']
		else:
			raise Exception("Error in tracker.get_heartbeatinterval: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def get_version(self):
		
		"""Returns the version number (integer)
		"""
		
		# send the request
		response = self.connection.request('tracker', 'get', ['version'])
		# return value or error
		if response['statuscode'] == 200:
			return response['values']['version']
		else:
			raise Exception("Error in tracker.get_version: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def get_trackerstate(self):
		
		"""Returns the state of the physcial tracker (integer):
			0:	TRACKER_CONNECTED
				tracker is detected and working
			1:	TRACKER_NOT_CONNECTED
				tracker device is not connected
			2:	TRACKER_CONNECTED_BADFW
				tracker device is connected, but not working due to
				bad firmware
			3:	TRACKER_CONNECTED_NOUSB3
				tracker device is connected, but not working due to
				unsupported USB host
			4:	TRACKER_CONNECTED_NOSTREAM
				tracker device is connected, but no stream could be
				received
		"""
		
		# send the request
		response = self.connection.request('tracker', 'get', ['trackerstate'])
		# return value of error
		if response['statuscode'] == 200:
			return response['values']['trackerstate']
		else:
			raise Exception("Error in tracker.get_trackerstate: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def get_framerate(self):
		
		"""Returns the frame rate that the tracker is running at (integer)
		"""
		
		# send the request
		response = self.connection.request('tracker', 'get', ['framerate'])
		# return value or error
		if response['statuscode'] == 200:
			return response['values']['framerate']
		else:
			raise Exception("Error in tracker.get_framerate: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def get_iscalibrated(self):
		
		"""Indicates whether there is a calibration (Boolean)
		"""
		
		# send the request
		response = self.connection.request('tracker', 'get', ['iscalibrated'])
		# return value or error
		if response['statuscode'] == 200:
			return response['values']['iscalibrated'] == 'true'
		else:
			raise Exception("Error in tracker.get_iscalibrated: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def get_iscalibrating(self):
		
		"""Indicates whether the tracker is in calibration mode (Boolean)
		"""
		
		# send the request
		response = self.connection.request('tracker', 'get', ['iscalibrating'])
		# return value or error
		if response['statuscode'] == 200:
			return response['values']['iscalibrating'] == 'true'
		else:
			raise Exception("Error in tracker.get_iscalibrating: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def get_frame(self):
		
		"""Returns the latest frame data (dict)
			{	'timestamp': string time representation,
				'time': integer timestamp in milliseconds,
				'fix': Boolean indicating whether there is a fixation,
				'state': integer 32bit masked tracker state,
				'rawx': integer raw x gaze coordinate in pixels,
				'rawy': integer raw y gaze coordinate in pixels,
				'avgx': integer smoothed x gaze coordinate in pixels,
				'avgx': integer smoothed y gaze coordinate in pixels,
				'psize': float average pupil size,
				'Lrawx': integer raw x left eye gaze coordinate in pixels,
				'Lrawy': integer raw y left eye gaze coordinate in pixels,
				'Lavgx': integer smoothed x left eye gaze coordinate in pixels,
				'Lavgx': integer smoothed y left eye gaze coordinate in pixels,
				'Lpsize': float left eye pupil size,
				'Lpupilx': integer raw left eye pupil centre x coordinate,
				'Lpupily': integer raw left eye pupil centre y coordinate,
				'Rrawx': integer raw x right eye gaze coordinate in pixels,
				'Rrawy': integer raw y right eye gaze coordinate in pixels,
				'Ravgx': integer smoothed x right eye gaze coordinate in pixels,
				'Ravgx': integer smoothed y right eye gaze coordinate in pixels,
				'Rpsize': float right eye pupil size,
				'Rpupilx': integer raw right eye pupil centre x coordinate,
				'Rpupily': integer raw right eye pupil centre y coordinate,
				}
		"""
		
		# send the request
		response = self.connection.request('tracker', 'get', ['iscalibrated'])
		# raise error if needed
		if response['statuscode'] != 200:
			raise Exception("Error in tracker.get_iscalibrated: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
		# parse response
		return {	'timestamp':	response['values']['frame']['timestamp'],
				'time':		response['values']['frame']['time'],
				'fix':		response['values']['frame']['fix']=='true',
				'state':		response['values']['frame']['state'],
				'rawx':		response['values']['frame']['raw']['x'],
				'rawy':		response['values']['frame']['raw']['y'],
				'avgx':		response['values']['frame']['avg']['x'],
				'avgy':		response['values']['frame']['avg']['y'],
				'psize':		(response['values']['frame']['lefteye']['psize']+response['values']['frame']['righteye']['psize'])/2.0,
				'Lrawx':		response['values']['frame']['lefteye']['raw']['x'],
				'Lrawy':		response['values']['frame']['lefteye']['raw']['y'],
				'Lavgx':		response['values']['frame']['lefteye']['avg']['x'],
				'Lavgy':		response['values']['frame']['lefteye']['avg']['y'],
				'Lpsize':		response['values']['frame']['lefteye']['psize'],
				'Lpupilx':	response['values']['frame']['lefteye']['pcenter']['x'],
				'Lpupily':	response['values']['frame']['lefteye']['pcenter']['y'],
				'Rrawx':		response['values']['frame']['righteye']['raw']['x'],
				'Rrawy':		response['values']['frame']['righteye']['raw']['y'],
				'Ravgx':		response['values']['frame']['righteye']['avg']['x'],
				'Ravgy':		response['values']['frame']['righteye']['avg']['y'],
				'Rpsize':		response['values']['frame']['righteye']['psize'],
				'Rpupilx':	response['values']['frame']['righteye']['pcenter']['x'],
				'Rpupily':	response['values']['frame']['righteye']['pcenter']['y']
				}
	
	def get_screenindex(self):
		
		"""Returns the screen index number in a multi screen setup (integer)
		"""
		
		# send the request
		response = self.connection.request('tracker', 'get', ['screenindex'])
		# return value or error
		if response['statuscode'] == 200:
			return response['values']['screenindex']
		else:
			raise Exception("Error in tracker.get_screenindex: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def get_screenresw(self):
		
		"""Returns the screen resolution width in pixels (integer)
		"""
		
		# send the request
		response = self.connection.request('tracker', 'get', ['screenresw'])
		# return value or error
		if response['statuscode'] == 200:
			return response['values']['screenresw']
		else:
			raise Exception("Error in tracker.get_screenresw: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def get_screenresh(self):
		
		"""Returns the screen resolution height in pixels (integer)
		"""
		
		# send the request
		response = self.connection.request('tracker', 'get', ['screenresh'])
		# return value or error
		if response['statuscode'] == 200:
			return response['values']['screenresh']
		else:
			raise Exception("Error in tracker.get_screenresh: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def get_screenpsyw(self):
		
		"""Returns the physical screen width in meters (float)
		"""
		
		# send the request
		response = self.connection.request('tracker', 'get', ['screenpsyw'])
		# return value or error
		if response['statuscode'] == 200:
			return response['values']['screenpsyw']
		else:
			raise Exception("Error in tracker.get_screenpsyw: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def get_screenpsyh(self):
		
		"""Returns the physical screen height in meters (float)
		"""
		
		# send the request
		response = self.connection.request('tracker', 'get', ['screenpsyh'])
		# return value or error
		if response['statuscode'] == 200:
			return response['values']['screenpsyh']
		else:
			raise Exception("Error in tracker.get_screenpsyh: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def set_push(self, push=None):
		
		"""Toggles the push state, or sets the state to the passed value
		
		keyword arguments
		
		push		--	Boolean indicating the state: True for push,
											False for pull
											None to toggle current
		returns
		
		state	--	Boolean indicating the push state
		"""
		
		# check passed value
		if push == None:
			# toggle state
			self.push = self.push != True
		elif type(push) == bool:
			# set state to passed value
			self.push = push
		else:
			# error on anything other than None, True or False
			raise Exception("tracker.set_push: push keyword argument should be a Boolean or None, not '%s'" % push)
		
		# send the request
		response = self.connection.request('tracker', 'set', {'push':str(self.push).lower()})
		# return value or error
		if response['statuscode'] == 200:
			return self.push
		else:
			raise Exception("Error in tracker.set_push: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	
	def set_version(self, version):
		
		"""Set the protocol version
		
		arguments
		
		version	--	integer version number
		"""
		
		# send the request
		response = self.connection.request('tracker', 'set', {'version':version})
		# return value or error
		if response['statuscode'] == 200:
			return version
		else:
			raise Exception("Error in tracker.set_version: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def set_screenindex(self, index):
		
		"""Set the screen index
		
		arguments
		
		index	--	integer value indicating the index number of the
					screen that is to be used with the tracker
		"""
		
		# send the request
		response = self.connection.request('tracker', 'set', {'screenindex':index})
		# return value or error
		if response['statuscode'] == 200:
			return index
		else:
			raise Exception("Error in tracker.set_screenindex: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def set_screenresw(self, width):
		
		"""Set the screen resolution width
		
		arguments
		
		width	--	integer value indicating the screen resolution width
					in pixels
		"""
		
		# send the request
		response = self.connection.request('tracker', 'set', {'screenresw':width})
		# return value or error
		if response['statuscode'] == 200:
			return width
		else:
			raise Exception("Error in tracker.set_screenresw: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def set_screenresh(self, height):
		
		"""Set the screen resolution height
		
		arguments
		
		height	--	integer value indicating the screen resolution height
					in pixels
		"""
		
		# send the request
		response = self.connection.request('tracker', 'set', {'screenresh':height})
		# return value or error
		if response['statuscode'] == 200:
			return height
		else:
			raise Exception("Error in tracker.set_screenresh: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def set_screenpsyw(self, width):
		
		"""Set the physical width of the screen
		
		arguments
		
		width	--	float value indicating the physical screen width in
					metres
		"""
		
		# send the request
		response = self.connection.request('tracker', 'set', {'screenpsyw':width})
		# return value or error
		if response['statuscode'] == 200:
			return width
		else:
			raise Exception("Error in tracker.set_screenpsyw: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def set_screenpsyh(self, height):
		
		"""Set the physical height of the screen
		
		arguments
		
		width	--	float value indicating the physical screen height in
					metres
		"""
		
		# send the request
		response = self.connection.request('tracker', 'set', {'screenpsyh':height})
		# return value or error
		if response['statuscode'] == 200:
			return height
		else:
			raise Exception("Error in tracker.set_screenpsyh: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))


class calibration:
	
	"""class for calibration related requests"""
	
	def __init__(self, connection):
		
		"""Initializes a calibration instance
		
		arguments
		
		connection	--	a pytribe.connection instance for the currently
						attached EyeTribe tracker
		"""
		
		self.connection = connection
	
	def set_connection(self, connection):
		
		"""Set a new connection
		
		arguments
		
		connection	--	a pytribe.connection instance for the currently
						attached EyeTribe tracker
		"""
		
		self.connection = connection
	
	def start(self, pointcount=9):
		
		"""Starts the calibration, using the passed number of calibration
		points
		
		keyword arguments
		
		pointcount	--	integer value indicating the amount of
						calibration points that should be used, which
						should be at least 7 (default = 9)
		"""
		
		# send the request
		response = self.connection.request('calibration', 'start', {'pointcount':pointcount})
		# return value or error
		if response['statuscode'] == 200:
			return True
		else:
			raise Exception("Error in calibration.start: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def pointstart(self, x, y):
		
		"""Mark the beginning of a new calibration point for the tracker to
		process
		
		arguments

		x			--	integer indicating the x coordinate of the
						calibration point
		y			--	integer indicating the y coordinate of the
						calibration point
		
		returns

		success		--	Boolean: True on success, False on a failure
		"""
		
		# send the request
		response = self.connection.request('calibration', 'pointstart', {'x':x,'y':y})
		# return value or error
		if response['statuscode'] == 200:
			return True
		else:
			raise Exception("Error in calibration.pointstart: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def pointend(self):
		
		"""Mark the end of processing a calibration point
		
		returns
		calibresults	--	a dict containing the calibration results:
						{	'result':	Boolean indicating whether the
									calibration was succesful
							'deg':	float indicating the average error
									in degrees of visual angle
							'Ldeg':	float indicating the left eye
									error in degrees of visual angle
							'Rdeg':	float indicating the right eye
									error in degrees of visual angle
							'calibpoints': list, containing a dict for
										each calibration point:
										{'state':	integer indicating
												the state of the
												calibration point
												(0 means no useful
												data has been
												obtained and the
												point should be
												resampled; 1 means
												the data is of
												questionable
												quality, consider
												resampling; 2 means
												the data is ok)
										'cpx':	x coordinate of the
												calibration point
										'cpy':	y coordinate of the
												calibration point
										'mecpx':	mean estimated x
												coordinate of the
												calibration point
										'mecpy':	mean estimated y
												coordinate of the
												calibration point
										'acd':	float indicating
												the accuracy in
												degrees of visual
												angle
										'Lacd':	float indicating
												the accuracy in
												degrees of visual
												angle (left eye)
										'Racd':	float indicating
												the accuracy in
												degrees of visual
												angle (right eye)
										'mepix':	mean error in
												pixels
										'Lmepix':	mean error in
												pixels (left eye)
										'Rmepix':	mean error in
												pixels (right eye)
										'asdp':	standard deviation
												in pixels
										'Lasdp':	standard deviation
												in pixels (left eye)
										'Rasdp':	standard deviation
												in pixels (right eye)
										}
						}
		"""
		
		# send the request
		response = self.connection.request('calibration', 'pointend', None)
		# return value or error
		if response['statuscode'] != 200:
			raise Exception("Error in calibration.pointend: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
		# return calibration dict
		returndict =  {	'result':response['value']['calibresult']['result'],
						'deg':response['value']['calibresult']['deg'],
						'Rdeg':response['value']['calibresult']['degl'],
						'Ldeg':response['value']['calibresult']['degr'],
						'calibpoints':[]
						}
		for pointdict in response['value']['calibresult']['calibpoints']:
			returndict['calibpoints'].append({	'state':pointdict['state'],
										'cpx':pointdict['cp']['x'],
										'cpy':pointdict['cp']['y'],
										'mecpx':pointdict['mecp']['x'],
										'mecpy':pointdict['mecp']['y'],
										'acd':pointdict['acd']['ad'],
										'Lacd':pointdict['acd']['adl'],
										'Racd':pointdict['acd']['adr'],
										'mepix':pointdict['mepix']['mep'],
										'Lmepix':pointdict['mepix']['mepl'],
										'Rmepix':pointdict['mepix']['mepr'],
										'asdp':pointdict['asdp']['asd'],
										'Lasdp':pointdict['asdp']['asdl'],
										'Rasdp':pointdict['asdp']['asdr']
										})
		return returndict
	
	def abort(self):
		
		"""Cancels the ongoing sequence and reinstates the previous
		calibration (only if there is one!)
		
		returns
		
		success		--	Boolean: True on success, False on failure
		"""
		
		# send the request
		response = self.connection.request('calibration', 'abort', None)
		# return value or error
		if response['statuscode'] == 200:
			return True
		else:
			raise Exception("Error in calibration.abort: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))
	
	def clear(self):
		
		"""Removes the current calibration from the tracker
		
		returns
		
		success		--	Boolean: True on success, False on failure
		"""

		# send the request
		response = self.connection.request('calibration', 'clear', None)
		# return value or error
		if response['statuscode'] == 200:
			return True
		else:
			raise Exception("Error in calibration.clear: %s (code %d)" % (response['values']['statusmessage'],response['statuscode']))


class heartbeat:
	
	"""class for signalling heartbeats to the server"""
	
	def __init__(self, connection):
		
		"""Initializes a heartbeat instance (not implemented in the SDK yet)
		
		arguments
		
		connection	--	a pytribe.connection instance for the currently
						attached EyeTribe tracker
		"""
		
		self.connection = connection
	
	def set_connection(self, connection):
		
		"""Set a new connection
		
		arguments
		
		connection	--	a pytribe.connection instance for the currently
						attached EyeTribe tracker
		"""
		
		self.connection = connection