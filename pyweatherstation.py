#!/usr/bin/env python
#
# PyWeatherStation provides an interface between Davis Vantage Pro2 and Raspberry Pi to 
# report weather data to Weather Underground
#
# Author : René Desgagnés
# Email: rene.desgagnes@gmail.com
# Date : September 22th 2015

import os
import sys
import time
import logging
import logging.handlers
import argparse

import weather.station
import weather.services
import http.client


class NoDeviceException(Exception):pass
class NoDeviceExceptionError(NoDeviceException,TypeError):pass


LOG_FILENAME = "/var/log/PyWeatherStation.log"
LOG_LEVEL = logging.WARNING
log = logging.getLogger(__name__)
POSTING_INTERVAL_TIME = 60
NUMBER_OF_UPDATES_IN_A_DAY= (24 * 3600)/POSTING_INTERVAL_TIME
NUMBER_OF_NTP_UPDATES = 60


def weather_update(publishSite,LOOP1,LOOP2):
	#print ("entering weather_update")		
	now = time.gmtime()
	LOOP2['DateStampUTC']  = time.strftime("%Y-%m-%d %H:%M:%S", now)
	#print("dewpoint: ",LOOP2['DewPoint'])
	#try:
         #print ("pressure : ",LOOP1['Pressure'])
         #print ("dewPoint : ",LOOP1['DewPoint'])
         #print ("humidity : ",LOOP1['OutHumidity'])
         #print("tempf : ",LOOP1['OutTemp'])
         #print ("rainin : ",LOOP1['RainRate'])
         #print ("rainday : ",LOOP1['DayRain'])
          #      print ("dateutc : ",LOOP2['DateStampUTC'])
          #      print ("windspeed : ",LOOP1['10MinAvgWindSpeed'])
          #      print ("winddir : ",LOOP1['WindDir'])
          #      print ("windgust : ", LOOP2['10MinWindGust'])
          #      print ("windgustdir : ",LOOP2['WindDir10MinGust'])
	#print ("solarradiation : ",LOOP2['SolarRadiation'])
	#print ("UV : ",LOOP2['UVIndex'])
	response=""
	try:
		publishSite.set(
			pressure = LOOP1['Pressure'],
			dewpoint = LOOP2['DewPoint'],
			humidity = LOOP1['OutHumidity'],
			tempf    = LOOP1['OutTemp'],
			rainin   = LOOP1['RainRate'],
			rainday  = LOOP1['DayRain'],
			dateutc = LOOP2['DateStampUTC'],
			windspeed= LOOP1['WindSpeed'],
			windspeedAvg2m = LOOP2['2MinAvgWindSpeed'],
			winddir  = LOOP2['WindDir'],
			windgust = LOOP2['10MinWindGust'],
			windgustdir = LOOP2['WindDir10MinWindGust'],
			windgustspeed10m =LOOP2['10MinWindGust'],
			windgustdir10m = LOOP2['WindDir10MinWindGust'],
			solarradiation = LOOP2['SolarRadiation'],
			UV = LOOP2['UVIndex']
			)
#		print ("solarradiation: ",publishSite.solarradiation)
		log.info("Posting update to WUnderground")
		response = publishSite.publish()
		log.info("Posting response %s",response)
		#print("Posting response %s",response)
	except (http.client.HTTPException) as e:
		log.warn('publisher %s: %s'%(publishSite.__class__.__name__,e))
		response = publishSite.publish()
#		log.warn("publisher response %s",response)



def init_log(debug):

	
#	from logging.handlers import SysLogHandler
#	fmt = logging.Formatter( os.path.basename(sys.argv[0]) + 
#	".%(name)s %(levelname)s - %(message)s")
	
#	facility = SysLogHandler.LOG_DAEMON 
#	syslog = SysLogHandler(address='/dev/log',facility=facility)
#	syslog.setFormatter(fmt)
#	log.addHandler(syslog)
#	if not quiet :
#		console = logging.StreamHandler()
#		console.setFormatter(fmt)
#		log.addHandler(console)
#		log.setLevel(logging.INFO)
#		if debug :
#			log.setLevel(logging.DEBUG)
	if debug:	
		log.setLevel(logging.DEBUG)
		
	else:
		log.setLevel(LOG_LEVEL)
		

	handler = logging.handlers.TimedRotatingFileHandler(LOG_FILENAME,when="midnight",backupCount=3)
	formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
	handler.setFormatter(formatter)
	log.addHandler(handler)
	



def setParsingOptions(parser):

	parser.add_argument('-t','--tty',dest='tty',default='/dev/ttyAMA0',
	help='set serial port device [/dev/ttyS0]')
	parser.add_argument('-d','--debug',dest='debug',action="store_true", default=False,
	help='enable debug logging')
	#parser.add_argument('-q','--quiet',dest='quiet',action="store_true",default=False,
	#help='disable console logging')
	parser.add_argument('-l','--log',dest='LOG_FILENAME',default=LOG_FILENAME,help="file to write log to (default " + LOG_FILENAME + ")" )


def 	main():

	parser = argparse.ArgumentParser(description='Davis Vantage Pro2 weather station interface to Weather Underground')
	setParsingOptions(parser)
	args = parser.parse_args()
	log.debug("Arguments ", args)
	init_log(args.debug)
	loopCounter = 0
	ps = weather.services.Wunderground('IALBERTA483','reergnyd')
		
	try:
		station = weather.station.VantagePro2()
	
		while (True):
			
			station.serialComm(args.tty)

			if(station.serialCommStatus() == True):
				#print("ici");
				station.getConsoleID()
				station.getConsoleFirmwareDateCode()
				station.getConsoleFirmwareVersion()
				log.info("Console type is %s .",station.getConsoleType())
		
		#while (True):
				if(loopCounter % NUMBER_OF_NTP_UPDATES == 0 ):
					station.setConsoleTime()
					loopCounter = 0
				LOOPResults  = station.getLOOPMsg()
				LOOP2Results = station.getLOOP2Msg()
				#print('loop results ',LOOPResults[0],LOOP2Results[0])
				#print('loop data ',LOOPResults[1])
				if( LOOPResults[0] == 100  and LOOP2Results[0] ==  100 ):
					weather_update(ps,LOOPResults[1],LOOP2Results[1])
					#print("posting")
				loopCounter = loopCounter + 1
			#print("avant sleep 60 secondes");
			time.sleep(POSTING_INTERVAL_TIME)
			#print("apres sleep 60 secondes");
#		while True:
#	
#			station.wakeupConsole()	
#			if(loopCounter % NUMBER_OF_UPDATES_IN_A_DAY == 0 and not loopCounter == 0):
#				station.setConsoleTime()
#				loopCounter = 0
#			LOOPResults = station.getLOOPMsg()
#			LOOP2Results = station.getLOOP2Msg()		
#			weather_update(ps,LOOPResults,LOOP2Results)
#			loopCounter = loopCounter + 1
#			time.sleep(60)
	
	except (Exception) as e:
		log.error(e,exc_info=True)
	

if __name__ == '__main__':

	main()







