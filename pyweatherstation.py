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
import argparse

import weather.station
import weather.services

log = logging.getLogger('')

class NoDeviceException(Exception):pass
class NoDeviceExceptionError(NoDeviceException,TypeError):pass


def weather_update(publishSite,LOOP1,LOOP2):
	print ("entering weather_update")		
	now = time.gmtime()
	LOOP2['DateStampUTC']  = time.strftime("%Y-%m-%d %H:%M:%S", now)
	print("dewpoint: ",LOOP2['DewPoint'])
	#try:
         #print ("pressure : ",LOOP1['Pressure'])
         #print ("dewPoint : ",LOOP1['DewPoint'])
         #print ("humidity : ",LOOP1['OutHumidity'])
         #print ("tempf : ",LOOP1['OutTemp'])
         #print ("rainin : ",LOOP1['RainRate'])
         #print ("rainday : ",LOOP1['DayRain'])
          #      print ("dateutc : ",LOOP2['DateStampUTC'])
          #      print ("windspeed : ",LOOP1['10MinAvgWindSpeed'])
          #      print ("winddir : ",LOOP1['WindDir'])
          #      print ("windgust : ", LOOP2['10MinWindGust'])
          #      print ("windgustdir : ",LOOP2['WindDir10MinGust'])
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
			winddir  = LOOP2['WindDir'],
			windgust = LOOP2['10MinWindGust'],
			windgustdir = LOOP2['WindDir10MinWindGust'],
			)
		response = publishSite.publish()
		print ("%s %s",response.status,response.reason)
	except (Exception) as e:
		log.warn('publisher %s: %s'%(ps.__class__.__name__,e))



def init_log(quiet,debug):

	from logging.handlers import SysLogHandler
	fmt = logging.Formatter( os.path.basename(sys.argv[0]) + 
	".%(name)s %(levelname)s - %(message)s")
	
	facility = SysLogHandler.LOG_DAEMON 
	syslog = SysLogHandler(address='/dev/log',facility=facility)
	syslog.setFormatter(fmt)
	log.addHandler(syslog)
	if not quiet :
		console = logging.StreamHandler()
		console.setFormatter(fmt)
		log.addHandler(console)
		log.setLevel(logging.INFO)
		if debug :
			log.setLevel(logging.DEBUG)


def setParsingOptions(parser):

	parser.add_argument('-t','--tty',dest='tty',default='/dev/ttyAMA0',
	help='set serial port device [/dev/ttyS0]')
	parser.add_argument('-d','--debug',dest='debug',action="store_true", default=False,
	help='enable debug logging')
	parser.add_argument('-q','--quiet',dest='quiet',action="store_true",default=False,
	help='disable console logging')

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Davis Vantage Pro2 weather station interface to Weather Underground')
	setParsingOptions(parser)
	args = parser.parse_args()
	print("Arguments ", args)
	init_log(args.quiet,args.debug)
	#log.info('test logging')
	
	ps = weather.services.Wunderground('IALBERTA483','reergnyd')
	
	station = weather.station.VantagePro2(args.tty)
	
	while True:
	
		try:		
			station.wakeUpConsole()	
			LOOPResults = station.getLOOPMsg()
			LOOP2Results = station.getLOOP2Msg()		
			weather_update(ps,LOOPResults,LOOP2Results)
			time.sleep(15)
		except (Exception) as e:
			log.error(e)









