
#Allows data query of Davis Vantage Pro2
#

from __future__ import absolute_import

from ._struct import Struct

import logging
import serial
import struct
import time
from array import array
import binascii
#import ntplib
from time import ctime

log = logging.getLogger('__main__'+'.'+__name__)

READ_DELAY = 3
BAUDRATE = 19200
STATION_DELAY = 0.3





def log_raw(msg,raw):
	#hex_raw = binascii.hexlify(raw)
	#print ("Size raw : ",len(raw))
	str=""
	for i in range(len(raw)):
		if(i == len(raw)-1):
			str+='{0:#X}'.format(raw[i])
		else:
			str+='{0:#X}'.format(raw[i])+','
	log.debug(msg + ': ' + str)
	
 
class NoDeviceException(Exception): pass


class VProCRC(object):
    '''
    Implements CRC algorithm, necessary for encoding and verifying data from
    the Davis Vantage Pro unit.
    '''

    CRC_TABLE = (
        0x0, 0x1021, 0x2042, 0x3063, 0x4084, 0x50a5, 0x60c6, 0x70e7,
        0x8108, 0x9129, 0xa14a, 0xb16b, 0xc18c, 0xd1ad, 0xe1ce, 0xf1ef,
        0x1231, 0x210, 0x3273, 0x2252, 0x52b5, 0x4294, 0x72f7, 0x62d6,
        0x9339, 0x8318, 0xb37b, 0xa35a, 0xd3bd, 0xc39c, 0xf3ff, 0xe3de,
        0x2462, 0x3443, 0x420, 0x1401, 0x64e6, 0x74c7, 0x44a4, 0x5485,
        0xa56a, 0xb54b, 0x8528, 0x9509, 0xe5ee, 0xf5cf, 0xc5ac, 0xd58d,
        0x3653, 0x2672, 0x1611, 0x630, 0x76d7, 0x66f6, 0x5695, 0x46b4,
        0xb75b, 0xa77a, 0x9719, 0x8738, 0xf7df, 0xe7fe, 0xd79d, 0xc7bc,
        0x48c4, 0x58e5, 0x6886, 0x78a7, 0x840, 0x1861, 0x2802, 0x3823,
        0xc9cc, 0xd9ed, 0xe98e, 0xf9af, 0x8948, 0x9969, 0xa90a, 0xb92b,
        0x5af5, 0x4ad4, 0x7ab7, 0x6a96, 0x1a71, 0xa50, 0x3a33, 0x2a12,
        0xdbfd, 0xcbdc, 0xfbbf, 0xeb9e, 0x9b79, 0x8b58, 0xbb3b, 0xab1a,
        0x6ca6, 0x7c87, 0x4ce4, 0x5cc5, 0x2c22, 0x3c03, 0xc60, 0x1c41,
        0xedae, 0xfd8f, 0xcdec, 0xddcd, 0xad2a, 0xbd0b, 0x8d68, 0x9d49,
        0x7e97, 0x6eb6, 0x5ed5, 0x4ef4, 0x3e13, 0x2e32, 0x1e51, 0xe70,
        0xff9f, 0xefbe, 0xdfdd, 0xcffc, 0xbf1b, 0xaf3a, 0x9f59, 0x8f78,
        0x9188, 0x81a9, 0xb1ca, 0xa1eb, 0xd10c, 0xc12d, 0xf14e, 0xe16f,
        0x1080, 0xa1, 0x30c2, 0x20e3, 0x5004, 0x4025, 0x7046, 0x6067,
        0x83b9, 0x9398, 0xa3fb, 0xb3da, 0xc33d, 0xd31c, 0xe37f, 0xf35e,
        0x2b1, 0x1290, 0x22f3, 0x32d2, 0x4235, 0x5214, 0x6277, 0x7256,
        0xb5ea, 0xa5cb, 0x95a8, 0x8589, 0xf56e, 0xe54f, 0xd52c, 0xc50d,
        0x34e2, 0x24c3, 0x14a0, 0x481, 0x7466, 0x6447, 0x5424, 0x4405,
        0xa7db, 0xb7fa, 0x8799, 0x97b8, 0xe75f, 0xf77e, 0xc71d, 0xd73c,
        0x26d3, 0x36f2, 0x691, 0x16b0, 0x6657, 0x7676, 0x4615, 0x5634,
        0xd94c, 0xc96d, 0xf90e, 0xe92f, 0x99c8, 0x89e9, 0xb98a, 0xa9ab,
        0x5844, 0x4865, 0x7806, 0x6827, 0x18c0, 0x8e1, 0x3882, 0x28a3,
        0xcb7d, 0xdb5c, 0xeb3f, 0xfb1e, 0x8bf9, 0x9bd8, 0xabbb, 0xbb9a,
        0x4a75, 0x5a54, 0x6a37, 0x7a16, 0xaf1, 0x1ad0, 0x2ab3, 0x3a92,
        0xfd2e, 0xed0f, 0xdd6c, 0xcd4d, 0xbdaa, 0xad8b, 0x9de8, 0x8dc9,
        0x7c26, 0x6c07, 0x5c64, 0x4c45, 0x3ca2, 0x2c83, 0x1ce0, 0xcc1,
        0xef1f, 0xff3e, 0xcf5d, 0xdf7c, 0xaf9b, 0xbfba, 0x8fd9, 0x9ff8,
        0x6e17, 0x7e36, 0x4e55, 0x5e74, 0x2e93, 0x3eb2, 0xed1, 0x1ef0,
      )


    @staticmethod
    def get(data):
        '''
        return CRC calc value from raw serial data
        '''
        crc = 0
        for byte in array('B',data):
            crc = (VProCRC.CRC_TABLE[ (crc>>8) ^ byte ] ^ ((crc&0xFF) << 8))
        return crc


    @staticmethod
    def verify(data):
    #
    #perform CRC check on raw serial data, return true if valid.
    #a valid CRC == 0.
    #
     if len(data) == 0:
      return False
     crc = VProCRC.get(data)
     #print("CRC ",hex(crc))
     if crc: log.info("CRC Bad")
     else:  log.debug("CRC OK")
     return not crc


class VantagePro2LOOPStruct( Struct ):

	Format = (
		('LOO',		'3s'), ('BarTrend',	'B'), ('PacketType', 	'B'),
		('NextRecord', 	 'H'), ('Pressure', 	'H'), ('InsideTemp', 	'H'),
		('InsideHumid',	 'B'), ('OutTemp',	'h'), ('WindSpeed', 	'B'), 
		('10AvgWndSpd',	 'B'), ('WindDir',	'H'), ('ExtraTemps',   '7s'),
	        ('SoilTemp',    '4s'), ('LeafsTemp',   '4s'), ('OutHumidity',   'B'),
		('ExtraHumid',  '7s'), ('RainRate',     'H'), ('UVIndex',	'B'),
		('SolarRad',	 'H'), ('StormRain',	'H'), ('StartDateStorm','H'),
		('DayRain',	 'H'), ('MonthRain',	'H'), ('YearRain',	'H'),
		('ETDay',	 'H'), ('ETMonth',	'H'), ('ETYear',	'H'),
		('SoilMoisture','4s'), ('LeafWetness', '4s'), ('InsideAlarms',	'B'),
		('RainAlarms',	 'B'), ('OutAlarms',	'2s'), ('ExAlarmTmpHumd','8s'),
		('AlarmSoilLeaf','4s'),('TxBatteryStatus','B'), ('ConsoleBatteryVoltage','H'),
		('ForecastIcon', 'B'), ('ForecastRule','B'), ('SunriseTime', 	'H'),
		('SunsetTime',	 'H'), ('EOL',	       '2s'), ('CRC',		'H') )

	def __init__(self):
        	super(VantagePro2LOOPStruct,self).__init__(self.Format,'=')


	def _post_unpack(self,items):
        	
		items['Pressure']       = items['Pressure']   / 1000.0
		items['InsideTemp']     = items['InsideTemp']     /   10.0
		items['OutTemp']        = items['OutTemp']    /   10.0
		items['RainRate']       = items['RainRate']   /  100.0
		items['StormRain']      = items['StormRain']  /  100.0
		items['StartDateStorm'] = self._unpack_storm_date(items['StartDateStorm'])
		# rain totals
		items['DayRain']     = items['DayRain']   /  100.0
		items['MonthRain']   = items['MonthRain'] /  100.0
		items['YearRain']    = items['YearRain']  /  100.0
		# evapotranspiration totals
		items['ETDay']       = items['ETDay']     / 1000.0
		items['ETMonth']     = items['ETMonth']   /  100.0
		items['ETYear']      = items['ETYear']    /  100.0
		# soil moisture + leaf wetness
		items['SoilMoisture']   = struct.unpack('4B',items['SoilMoisture'])
		items['LeafWetness'] = struct.unpack('4B',items['LeafWetness'])
		# battery statistics
		items['ConsoleBatteryVoltage'] = items['ConsoleBatteryVoltage'] * 300 / 512.0 / 100.0
		# sunrise / sunset
		items['SunriseTime'] = self._unpack_time( items['SunriseTime'] )
		items['SunsetTime']  = self._unpack_time( items['SunsetTime'] )
		
		#UVIndex
		items['UVIndex'] = items['UVIndex'] / 10.0
		
		return items


	@staticmethod
	def _unpack_time( val ):
		'''
		given a packed time field, unpack and return "HH:MM" string.
		'''
		# format: HHMM, and space padded on the left.ex: "601" is 6:01 AM
		return "%02d:%02d" % divmod(val,100)  # covert to "06:01"

	@staticmethod
	def _unpack_storm_date( date ):
		'''
		given a packed storm date field, unpack and return 'YYYY-MM-DD' string.
		'''
		year  = (date & 0x7f) + 2000        # 7 bits
		day   = (date >> 7) & 0x01f         # 5 bits
		month = (date >> 12) & 0x0f         # 4 bits
		return "%s-%s-%s" % (year, month, day)
		


class VantagePro2LOOP2Struct( Struct ):

	Format = (
		('LOO',		'3s'), ('BarTrend',	'B'), ('PacketType', 	'B'),
		('Unused', 	 'H'), ('Pressure', 	'H'), ('InsideTemp', 	'H'),
		('InsideHumid',	 'B'), ('OutTemp',	'h'), ('WindSpeed', 	'B'), 
		('Unused',	 'B'), ('WindDir',	'H'), ('10MinAvgWindSpeed',   'H'),
	        ('2MinAvgWindSpeed',    'H'), ('10MinWindGust',   'H'), ('WindDir10MinWindGust',  'H'),
		('Unused',       'H'), ('Unused',       'H'), ('DewPoint',	'h'),
		('Unused',	 'B'), ('OutHumidity',	'B'), ('Unused',        'B'),
		('HeatIndex',	 'h'), ('WindChill',	'h'), ('THISWIndex',	'h'),
		('RainRate',	 'H'), ('UVIndex',	'B'), ('SolarRadiation','H'),
		('StormRain',    'H'), ('StartDateStorm','H'), ('DailyRain',	'H'),
		('Last15MinRain','H'), ('LastHourRain',	'H'), ('DailyET',       'H'),
		('Last24HrRain', 'H'), ('BaroReduction','B'), ('UserBaroOffset','H'),
		('BaroCalib',   'H'), ('BaroSensorRaw','H'), ('AbsBaroPressure', 'H'),
		('Altimeter',    'H'), ('Unused',	 'H'), ('Next10MinWindSpeedGraph','B'),
		('Next15MinWindSpeedGraph','B'),('NextHourlyWindSpeedGraph','B'), ('NextDailyWindSpeedGraph','B'),
		('NextMinRainGraph','B'), ('NextRainStormGraph','B'), ('IndexMinHour', 'B'),
 		('NextMonthlyRain','B'),('NextYearlyRain','B'), ('NextSeasonalRain','B'),
		('Unused',      '6H'), ('EOL',          'H'), ('CRC',            'H'),  
		)

	def __init__(self):
        	super(VantagePro2LOOP2Struct,self).__init__(self.Format,'=')


	def _post_unpack(self,items):
        	
		items['Pressure']       = items['Pressure']   / 1000.0
		items['InsideTemp']     = items['InsideTemp']     /   10.0
		items['OutTemp']        = items['OutTemp']    /   10.0
		items['RainRate']       = items['RainRate']   /  100.0
		items['StormRain']      = items['StormRain']  /  100.0
		items['StartDateStorm'] = self._unpack_storm_date(items['StartDateStorm'])
		# wind stuff
		items['2MinAvgWindSpeed'] = items['2MinAvgWindSpeed'] / 10.0
		items['10MinWindGust'] = items['10MinWindGust'] / 10.0
		# rain totals
		items['DailyRain']     = items['DailyRain']   /  100.0
		# evapotranspiration totals
		items['DailyET']       = items['DailyET']     / 1000.0
		# Baro stuff
		items['UserBaroOffset'] = items['UserBaroOffset'] / 1000.0
		items['BaroCalib']     = items['BaroCalib'] / 1000.0
		items['BaroSensorRaw']  = items['BaroSensorRaw'] / 1000.0
		items['Altimeter']      = items['Altimeter'] / 1000.0
						
		#UVIndex
		items['UVIndex'] = items['UVIndex'] / 10.0

		return items


	@staticmethod
	def _unpack_time( val ):
		'''
		given a packed time field, unpack and return "HH:MM" string.
		'''
		# format: HHMM, and space padded on the left.ex: "601" is 6:01 AM
		return "%02d:%02d" % divmod(val,100)  # covert to "06:01"

	@staticmethod
	def _unpack_storm_date( date ):
		'''
		given a packed storm date field, unpack and return 'YYYY-MM-DD' string.
		'''
		year  = (date & 0x7f) + 2000        # 7 bits
		day   = (date >> 7) & 0x01f         # 5 bits
		month = (date >> 12) & 0x0f         # 4 bits
		return "%s-%s-%s" % (year, month, day)


class VantagePro2HILOWStruct( Struct ):

	Format = (
		('DailyLowBarometer', 'H'), ('DailyHighBarometer', 'H'), ('MonthLowBar', 'H'),
		('MonthHighBar',      'H'), ('YearLowBarometer',   'H'), ('YearHighBarometer', 'H'),
		('TimeDayLowBar',     'H'), ('TimeDayHighBar',     'H'), ('DailyHiWindSpeed',  'B'),
		('TimeHiSpeed',       'H'), ('MonthHiSpeed',       'B'), ('YearHiWindSpeed',   'B'),
		('DayHiInsideTemp',   'H'), ('DayLowInsideTemp',   'H'), ('TimeDayHiInsideTemp', 'H'),
		('TimeDayLowInsideTemp', 'H'), ('MonthLowInsideTemp','H'), ('MonthHiInsideTemp','H'),
		('YearLowInsideTemp', 'H'), ('YearHiInsideTemp',   'H'), ('DayHiInsideHumidity','B'),
		('DayLowInsideHumidity','B'), ('TimeDayHiInsideHumidity','H'), ('TimeDayLowInsideHumidity','H'),
		('MonthHiInsideHumidity','B'), ('MonthLowInsideHumidity','B'), ('YearHiInsideHumidity', 'B'),
		('YearLowInsideHumidity', 'B'), ('DayLowOutsideTemp', 'H'), ('DayHiOutsideTemp', 'H'),
		('TimeDayLowOutsideTemp', 'H'), ('TimeDayHiOutsideTemp','H'), ('MonthHiOutsideTemp', 'H'),
		('MonthLowOutsideTemp', 'H'), ('YearHiOutsideTemp', 'H'), ('YearLowOutsideTemp', 'H'),
		('DayLowDewPoint',    'H'), ('DayHiDewPoint',       'H'), ('TimeDayLowDewPoint' , 'H'),
		('TimeDayHiDeewPoint', 'H'), ('MonthHiDewPoint',    'H'), ('MonthLowDewPoint',     'H'),
		('YearHiDewPoint',     'H'), ('YearLowDewPoint',    'H'), ('DayLowWindChill',      'H'),
		('TimeDayLowWindChill','H'), ('MonthLowWindChill',  'H'), ('YearLowWindChill', 'H'),
		('DayHighHeatIndex',   'H'), ('TimeDayHighHeatIndex','H'), ('YearHighHeatIndex' ,  'H'),
		('DayHighTHSW',        'H'), ('TimeDayHighTHSW',    'H'), ('YearHighTHSW',         'H'),
		('DayHighSolarRad',    'H'), ('TimeDayHighSolarRad','H'), ('MonthHighSolarRad',    'H'),
		('YearHighSolarRad',   'H'), ('DayHighUVIndex',     'B'), ('TimeDayHighUVIndex',   'H'),
		('MonthHighUVIndex',   'B'), ('YearHighUVIndex',    'B'), ('DayHighRainRate',      'H'),
		('TimeDayHighRainRate','H'), ('HourHighRainRate',   'H'), ('MonthHighRainRate',    'H'),
		('YearHighRainRate',   'H'), ('ExtraLeafSoilTempDayLowTemp', '15B'), ('ExtraLeafSoilTempDayHiTemp', '15B'),
		('ExtraLeafSoilTempTimeDayLowTemp', '15H'), ('ExtraLeafSoilTempTimeDayHiTemp', '15H'),('ExtraLeafSoilTempMonthHiTemp','15B'),
		('ExtraLeafSoilTempMonthLowTemp', '15B'), ('ExtraLeafSoilTempYearHiTemp', '15B'), ('ExtraLeafSoilTempYearLowTemp', '15B'),
		('DayLowHumidity',    '8B'), ('DayHighHumidity',   '8B'), ('TimeDayLowHumidity', '8H'), 
		('TimeDayHighHumidity','8H'), ('MonthHighHumidity', '8B'), ('MonthLowHumidity', '8B'),
		('YearLowHumidity',   '8B'), ('YearLowHumidity' ,    '8B'), ('DayHiSoilMoisture', '4B'),
		('TimeDayHighSoilMoisture','4H'), ('DayLowSoilMoisture','4B'), ('TimeDayLowSoilMoisture','4H'),
		('MonthLowSoilMoisture', '4B'), ('MonthHiSoilMoisture', '4B'), ('YearLowSoilMoisture', '4B'),
		('YearHiSoilMoisture', '4B'), ('DayHiLeafWetness', '4B'),  ('TimeDayHiLeafWetness', '4H'),
		('DayLowLeafWetness', '4B'), ('TimeDayLowLeafWetness', '4H'), ('MonthLowLeafWetness','4B'),
		('MonthHiLeafWetness', '4B'), ('YearLowLeafWetness' , '4B'), ('YearHiLeafWetness', '4B'),
		('CRC', 'H') )

	def __init__(self):
        	super(VantagePro2HILOWStruct,self).__init__(self.Format,'=')


	def _post_unpack(self,items):
        	
		items['Pressure']       = items['Pressure']   / 1000.0
		items['InsideTemp']     = items['InsideTemp']     /   10.0
		items['OutTemp']        = items['OutTemp']    /   10.0
		items['RainRate']       = items['RainRate']   /  100.0
		items['StormRain']      = items['StormRain']  /  100.0
		items['StartDateStorm'] = self._unpack_storm_date(items['StartDateStorm'])
		# rain totals
		items['DayRain']     = items['DayRain']   /  100.0
		# evapotranspiration totals
		items['DailyET']       = items['ETDay']     / 1000.0
		# Baro stuff
		items['UserBaroOffset'] = items['UserBaroOffset'] / 1000.0
		items['BaroCalib']     = items['BaroCalib'] / 1000.0
		items['BaroSensorRaw']  = items['BaroSensorRaw'] / 1000.0
		items['Altimeter']      = items['Altimeter'] / 1000.0
						
		return items


	@staticmethod
	def _unpack_time( val ):
		'''
		given a packed time field, unpack and return "HH:MM" string.
		'''
		# format: HHMM, and space padded on the left.ex: "601" is 6:01 AM
		return "%02d:%02d" % divmod(val,100)  # covert to "06:01"

	@staticmethod
	def _unpack_storm_date( date ):
		'''
		given a packed storm date field, unpack and return 'YYYY-MM-DD' string.
		'''
		year  = (date & 0x7f) + 2000        # 7 bits
		day   = (date >> 7) & 0x01f         # 5 bits
		month = (date >> 12) & 0x0f         # 4 bits
		return "%s-%s-%s" % (year, month, day)



LOOPStructObject  = VantagePro2LOOPStruct()
LOOP2StructObject = VantagePro2LOOP2Struct()
HILOWStructObject = VantagePro2HILOWStruct()	

class VantagePro2(object):

	#commands
	WAKEUPCMD = b'\n'
	LF = b'\n'
	CR = b'\r'
	#reply commands
	WAKEUPACK = b'\n\r'
	ACK = b'\x06'
	ESC = '\x1b'
	OK = b'\n\rOK\n\r'
	BADCRC =b'\x18'

	WRD = bytes([0x41,0x43,0x4B,0x16])
	WRDCmd = bytes([0x57,0x52,0x44,0x12,0x4D,0x0A])
	IDReply = bytes([0x0a,0x0d,0x36,0x33,0x31,0x32,0x43,0x0a,0x0d])
	port = None

	def __init__(self):
		#self.port = serial.Serial(device,BAUDRATE,timeout=READ_DELAY)		
		#self.wakeupConsole()		
		#self.getConsoleType()
		#self.getConsoleID()
		self.port=None
		
		
	def __del__(self):
		if(self.port != None):
			self.port.close()


	def serialCommStatus(self):
		if (self.port == None):
			return False
		else :
			return True

	def serialComm(self,device):
		
		#print("in serialComm")
		self.port = serial.Serial(device,BAUDRATE,timeout=READ_DELAY)
		time.sleep(STATION_DELAY)
	
		if self.port == None :
			return
		else :
			wakeUpSuccess = False
			for attemptNo in range(1,4):
				log.info("Sending wakeup command to Console. Attempt %d/3",attemptNo)
				#print("Range: %d/3",attemptNo)
				self.port.write(self.LF)
				if self.port.inWaiting() == 2:
					dummyBuffer = self.port.read(self.port.inWaiting())
					log.info("Console is awake after %d call(s).",attemptNo)
					wakeUpSuccess = True
					self.writeCommand("Test")
					time.sleep(STATION_DELAY)
					dummyBuffer = self.port.read(self.port.inWaiting())
					#print("console is awake")
					break
				else:
					log.info("The Console is not responding to wakeupcall")
					#print("console not awake")
					#dummyBuffer = self.port.read(self.port.inWaiting())
					time.sleep(1.5)

			if wakeUpSuccess == True:
				log.info("The Console is now responding to Commands.")
				#print("wakeupsuccess")
			else:
				log.info("Unable to wake up the console. Check connections.")
				self.port.close()
				self.port = None
				#print("self.port=None")
			return self.port
	  		
	def writeCommand(self,Command):
		if self.port != None:
	       		Command = Command.encode() + self.LF
	       	
		self.port.write(Command)

		if Command == "VER".encode() + self.LF:
			time.sleep(STATION_DELAY * 3)
		else:
		    	time.sleep(STATION_DELAY)

	    	
		
	def wakeupConsole(self):
		condition = True
		while(condition):
			for i in range(3):
				log.info("Sending Wakeup Command to Console. Attempt %d/3",i+1)
				#self.port.write(bytearray('\n','ascii'))
				self.port.write(self.LF)
				ack = self.port.read(len(self.WAKEUPACK))
				log_raw('read',ack)
				if ack == self.WAKEUPACK:
					log.debug("Console is awake after #%d call(s).",i+1)
					log.debug("Console is now responding to commands")
					condition = False
					break
				
			time.sleep(5)
		#raise NoDeviceException("Davis Vantage Pro2 is not responding to wakeup command.")

	def getConsoleID(self):
		idString = ""
		if self.port == None:
			log.info("No serial port handler (getConsoleID)")
			idString = "Not available."

		else:
			log.info("Sending ID Command to Console.")
			self.writeCommand("ID")
			idAck = self.port.inWaiting()
			
			if idAck > 0 :
				idString = self.port.read(idAck)
				log_raw('read',idString)
				idString = idString.decode().strip()
			if idString == "":
				idString = "Not available"
			
			log.info("Console ID is: %s",idString)
		
		return idString
		

	def getConsoleFirmwareDateCode(self):
		firmwareDateCode =""
		if self.port == None: 
			log.info("No serial port handler (getConsoleFirmwareDateCode)")
			firmwareDateCode = "Not Available"
			
		else:
			log.info("Sending VER Command to Console.")
			self.writeCommand("VER")
			firmwareDateCodeBytes = self.port.inWaiting()
			if firmwareDateCodeBytes > 0:
				firmwareDateCode = self.port.read(firmwareDateCodeBytes)
				log_raw('read',firmwareDateCode)
				firmwareDateCode = firmwareDateCode.decode()
				firmwareDateCode = firmwareDateCode.replace("\n\r","",5)
				firmwareDateCode = firmwareDateCode.replace("OK","",1)
				firmwareDateCode = firmwareDateCode.strip()
#			print("datecode: %s",firmwareDateCode)
			log.info("Console date code is %s .",firmwareDateCode)
		
		return firmwareDateCode
		
	def getConsoleFirmwareVersion(self):
		firmwareVersion =""
		if self.port == None: 
			log.info("No serial port handler (getConsoleFirmwareVersion)")
			firmwareVersion = "Not Available"
			
		else:
			log.info("Sending NVER Command to Console.")
			self.writeCommand("NVER")
			firmwareVersionBytes = self.port.inWaiting()
			if firmwareVersionBytes > 0 :
				firmwareVersion = self.port.read(firmwareVersionBytes)
				log_raw('read',firmwareVersion)
				firmwareVersion = firmwareVersion.decode()
				firmwareVersion = firmwareVersion.replace("\n\r","",3)
				firmwareVersion = firmwareVersion.replace("OK","",1)
				firmwareVersion = firmwareVersion.strip()
			log.info("Console version is %s .",firmwareVersion)
		
		return firmwareVersion

			

	def getConsoleType(self):
		log.info("Sending Console Type Command to Console.")
		#frame = bytearray([0x12,0x4D])
		self.writeCommand( "WRD" + chr(18) + chr(77) )
		#ack = self.port.read(len(self.ACK )+1)
		consoleTypeBytes = self.port.inWaiting()
		consoleType = ""
		if consoleTypeBytes == 2:
			consoleType = self.port.read(consoleTypeBytes)
		else:
			log.info("Ignoring WRD response from Console.")
			consoleType = "Unknown console type"
			return 	consoleType
		
		log_raw('read',consoleType)
		#ACK is 4 bytes <ACK><Model>
		if consoleType[0] == self.ACK:
			consoleType = consoleType[1]
		else:
			
			if consoleType != "" :

				if consoleType[1]== 0x00:
					log.info("Console is a Wizard III")
					consoleType="Console is a Wizard III"
					return consoleType
				elif consoleType[1] == 0x01:
					log.info("Console is a Wizard II")
					consoleType="Console is a Wizard II"
					return consoleType
				elif consoleType[1] == 0x02:
					log.info("Console is a Monitor")
					consoleType="Console is a Monitor"
					return consoleType
				elif consoleType[1] == 0x03 :
					log.info("Console is a Perception")
					consoleType="Console is a Perception"
					return consoleType
				elif consoleType[1] == 0x04:
					log.info("Console is a Gro Weather")
					consoleType="Console is a Gro Weather"
					return consoleType
				elif consoleType[1] == 0x05: 
					log.info("Console is Energy Enviromonitor")
					consoleType="Console is Energy Enviromonitor"
					return consoleType
				elif consoleType[1] == 0x06 :
					log.info("Console is Heatlh Enviromonitor")
					consoleType="Console is Health Enviromonitor"
					return consoleType
				elif consoleType[1] == 0x10:
					log.info("Console is a Vantage Pro, Vantage Pro2")
					consoleType="Console is Vantage Pro, Pro2"
					return consoleType
				elif consoleType[1] == 0x11 :
					log.info("Console is a Vantage Vue")
					consoleType="Console is a Vantage Vue"
					return consoleType
				else	:	
					log.info("Unknown console")
					consoleType="Unknownc console"
					return consoleType
							

	
	def setConsoleTime(self):
		
		if self.port == None :
			return
		else: 
			ntpTime = bytearray(6)
			log.info("Setting timestamp to %s",ctime(time.time()))
			localtime = time.localtime(time.time())
			#print("localtime: ", time.asctime(localtime))	
			ntpTime[0]=localtime.tm_sec
			ntpTime[1]=localtime.tm_min
			ntpTime[2]=localtime.tm_hour
			ntpTime[3]=localtime.tm_mday
			ntpTime[4]=localtime.tm_mon
			ntpTime[5]=localtime.tm_year - 1900
			crc = VProCRC.get(ntpTime)
		
			#format SETTIME<LF>
			#ACK
			#<seconds><minutes><hour><day><month><year-1900><CRC>
			log.info("Sending SETTIME Command to Console")
			self.port.flushInput()
			self.port.flushOutput()
			self.writeCommand("SETTIME")
			time.sleep(STATION_DELAY*3)
			ackBytes = self.port.inWaiting()
			if ackBytes != 1:
				self.port.flushInput()
				self.port.flushOutput()
				time.sleep(STATION_DELAY)
				self.writeCommand("SETTIME")
				time.sleep(STATION_DELAY*3)
				ackBytes = self.port.inWaiting()
			ack = self.port.read(ackBytes)
			log_raw("Read SETTIME First ACK",ack)
			if(ack == self.ACK):
				log.info("SETTIME first ack received")
			else:	
				log.info("SETTIME first ack not received")
			
			log.info("Sending time fields  to Console.")
#			print("write: ", ntpTime + crc.to_bytes(2,byteorder='big') )
			self.port.write(ntpTime + crc.to_bytes(2,byteorder='big')   )
			time.sleep(STATION_DELAY*3)
			ackBytes = self.port.inWaiting()
			ack = self.port.read(ackBytes)
			log_raw("Read SETTIME Second ACK",ack)
			if(ack == self.ACK):
				log.info("SETTIME Command success. Console is synch with NTP time %s.",time.asctime(localtime))
				
			elif(ack == self.BADCRC):
				log.info("BAD CRC Sent")
			
			return	
			


	def getLOOPMsg(self):
		
		loopMsgResponse = [0, 0]		

		if self.port == None :
			return loopMsgResponse
		else:
			log.info("Sending LOOP Command to Console.")
			self.writeCommand( "LOOP 1")
			time.sleep(STATION_DELAY*3)
			loopBytes = self.port.inWaiting()
			log.info("Got %d bytes from serial port",loopBytes)
			if(loopBytes != 100 ):
				log.info("Aborting LOOP 1 message read size %d",loopBytes)
				loopMsgResponse[1] = loopBytes
				return loopMsgResponse

			loop1Content = self.port.read(loopBytes)
			log_raw('read',loop1Content)
			loop1Content = loop1Content[1:]
			crc = VProCRC.verify(loop1Content)
			if( crc == False):
				log.info("Bad CRC for incoming LOOP packet.")
				loopMsgResponse[0] = 1
				return loopMsgReponse
			else:
				loopMsgResponse[0]=loopBytes
				loopMsgResponse[1]=LOOPStructObject.unpack(loop1Content)
				#print('loop1 data apres unpack ',loopMsgResponse[1])

				return loopMsgResponse
		
			
	def getLOOP2Msg(self):
		loopMsgResponse = [0,0]

		if self.port == None:
			return loopMsgResponse
		else:
			log.info("Sending LPS Command to Console.")
			self.port.flushInput()
			self.port.flushOutput()
			time.sleep(STATION_DELAY)
			self.writeCommand("\n\n")
			self.port.flushInput()
			self.writeCommand( "LPS 2 1")
			time.sleep(STATION_DELAY)
			loop2Bytes = self.port.inWaiting()
			log.info("Got %d bytes from serial port",loop2Bytes)
			if(loop2Bytes != 100):
				log.info("Aborting LPS message read size %d.",loop2Bytes)
				loopMsgResponse[0]= loop2Bytes
				return loopMsgResponse

			loop2Content = self.port.read(loop2Bytes)
			log_raw("read",loop2Content)
			loop2Content = loop2Content[1:]

			crc = VProCRC.verify(loop2Content)
			if( crc == False):
				log.info("Bad CRC for incoming LPS packet.")
				loopMsgResponse[0]=1
				return loopMsgResponse
			else:
				loopMsgResponse[0]=loop2Bytes
				loopMsgResponse[1]= LOOP2StructObject.unpack(loop2Content)
				return loopMsgResponse
			
								
	def getRXCHECK(self):
		
		for i in range(3):
			log.info("Sending RXCHECK Command to Console Attempt %d/3",i+1)
			self.port.write( ("RXCHECK").encode() + self.LF)
			ack = self.port.read(6)
			if(ack == NONE):
				raise NoDeviceException("Davis Vantage Pro2 is not responding to RXCHECK Command.")
			else :
				ack = self.port.read(6)
				log.info("RXCHECK Command Success.")
				log_raw("received",ack)
				break;
		

	def getHILOWSMsg(self):
		
		for i in range(3):
			log.info("Sending HILOWS Command to Console Attempt %d/3",i+1)
			self.port.write( ("HILOWS").encode() + self.LF)
			ack = self.port.read(1)
			if(ack != self.ACK):
				raise NoDeviceException("Davis Vantage Pro2 is not responding to HILOWS Command.")
			else :
				log.info("LPS HILOWS Command Success.")
				break;
		raw = self.port.read( HILOWSStructObject.size )
		log_raw('read',raw)
		crc = VProCRC.verify(raw)
		if( crc == false):
			raise NoDeviceException("Bad CRC for incoming HILOWS packet.")
		else:
			time.sleep(1)
			return HILOWSStructObject.unpack(raw)

			 

	#def sendCommand(self,cmd,*args,**kw):

	#	ok = kw.setdefault('ok',False)

	#	if args:
	#		cmd = "%s %s" % (cmd, ' '.join(str(a) for a in args))
		
	#	for i in range(3):
	#		log.info("Sending: %s. Attempt %d/3.",  cmd,i+1)
	#		self.port.write((cmd+'\n').encode())
	#		if ok:
	#			ack = self.port.read(len(self.OK)) 
	#			log_raw('read',ack)
	#			if ack == self.OK:
	#				return
	#		else:
	#			ack = self.port.read(len(self.ACK))
	#			log_raw('read',ack)
	#			if ack == self.ACK:
	#				return
	#	raise NoDeviceException("Davis Vantage Pro2 is not responding to %s command.",cmd)
			
									



