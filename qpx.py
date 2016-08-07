#!/usr/bin/python
'''

 Copyright (C) Alan Verdugo.

 Description:
	This program will use the Google QPX API to look for airplane tickets which 
	match certain criteria.

 Usage:
	python qpx.py --origin GDL --destination CUU --duration 30 --delay 30
	--solutions 3 --adult 1 --maxPrice USD55000

 Arguments:
	origin airport (The IATA code for the origin airport)
	origin date (The date when the travel starts, in CCYY-MM-DD)
	destination airport
	return date ()
	maxPrice (Maximum price allowed, in this format: USD99999)
	adult N (The number of adult passengers)
	duration N (duration of travel, in days) (only for round trips)

 Author:
	Alan Verdugo (alan@kippel.net)

 Creation date:
	2016-01-01 (?)

 Revision history:
	Author:		Date:		Notes:
	Alan		2016-06-08	Added this header.
	Alan        2016-06-11	Separated everything into functions.

'''

import requests							# To get results from QPX.
import json
import sys
from email.mime.text import MIMEText	# Some email modules we'll need.
import smtplib							# For the actual email sending.
from datetime import date, datetime, timedelta  # Date handling
import getopt							# To get arguments from CLI.

APIKEY = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
google_url = "https://www.googleapis.com/qpxExpress/v1/trips/search?key="+APIKEY
headers = {'content-type': 'application/json'}
qpx_home = "/home/ark/fun/python/qpx/"
responseCount = 0
resultsMessage = ""
global destinationCity
global originCity
global subjectDestinationCity
global subjectOriginCity
subjectDestinationCity = ""
subjectOriginCity = ""
subjectOriginAirportCity = ""
subjectDestinationAirportCity = ""

# Variables for sending notification email.
smtpServer = "localhost"					# The hostname of the SMTP server.
emailFrom = "QPXsearcher@localhost"					# Sender address.
emailFile = open(qpx_home + "mailList.txt", "r+")	# Dist. list, one address per line.
emailTo = emailFile.readlines()
emailFile.close() # Close file after reading the email recipients.

def help():
	print "Example of usage: python",sys.argv[0],("--origin GDL --destination CUU --duration 30 "
		"--delay 30 --solutions 3 --adult 1 --maxPrice USD55000")
	exit(0)

# Send email with results.
def sendEmail(resultsMessage,originCity,destinationCity,saleTotal):
	msg = MIMEText(resultsMessage,'plain')
	emailSubject = "Flights found: "+originCity+" to "+destinationCity+", "+destinationCity+" to "+originCity+" for "+saleTotal+" or less."
	msg['Subject'] = emailSubject
	s = smtplib.SMTP(smtpServer)
	s.sendmail(emailFrom, emailTo, msg.as_string())
	s.quit()


def getArgs(argv):
	global origin1
	global destination1
	global duration
	global delay
	global solutions
	global adultCount
	global maxPrice
	try:
		opts, args = getopt.getopt(argv,"ho:d:D:t:s:a:P:",["help","origin=","destination=","duration=","delay=","solutions=","adult=","maxPrice="])
	except getopt.GetoptError:
		exit(2)
	for opt, arg in opts:
		if opt in ("-h", "--help"):
			help()
		elif opt in ("-o","--origin"):
			origin1 = arg
		elif opt in ("-d","--destination"):
			destination1 = arg
		elif opt in ("-D","--duration"):
			duration = arg
		elif opt in ("-t","--delay"):
			delay = arg
		elif opt in ("-s","--solutions"):
			solutions = arg
		elif opt in ("-a","--adult"):
			adultCount = arg
		elif opt in ("-P","--maxPrice"):
			maxPrice = arg
	main()
			# Validate that the day argument is between 01 and 31.
			#try:
			#	datetime.datetime(year=int(year),month=int(month),day=int(day))
			#except:
			#	print "ERROR: Please provide a valid date."
			#	help()
			#	exit(3)

def main():
	global resultsMessage
	#resultsMessage == ""
	date1 = date.today() + timedelta(days=int(delay))
	# Variables used for the return trip (in round trips, obviously).
	origin2=destination1
	destination2=origin1
	date2 = date1 + timedelta(days=int(duration)) # Return date is departure date plus duration of travel.

	# Form the payload according to the arguments or default values.
	payload = '{"request":{"passengers":{"adultCount":'+adultCount+'},"slice":[{"origin":"'+origin1+'","destination":"'+destination1+'","date":"'+str(date1)+'"},{"origin":"'+origin2+'","destination":"'+destination2+'","date":"'+str(date2)+'"}],"maxPrice":"'+maxPrice+'","solutions":'+solutions+'}}'

	# Option 2: Read request from a .json file.
	#try:
	#	with open("./requestExample9.json") as json_file:
	#		payload = json.load(json_file)
	#except:
	#	print "Error reading file", json_file
	#	sys.exit(1)

	response = requests.post(google_url, data=payload, headers=headers)
	#response = requests.post(google_url, data=json.dumps(payload), headers=headers)

	# The status code should be 200 (success). Catch anything else and handle.
	if response.status_code != 200:
		print "FATAL ERROR: The response status code is:",response.status_code

	# Check if we don't have an empty result set.
	try:
		readableResponse = response.json()
	except ValueError:
		print datetime.today(), "ERROR: Empty result set. Payload:", payload
		sys.exit(2)

	# Check if there were no travel options returned.
	try:
		carrierList = readableResponse["trips"]["data"]["carrier"]
		airportList = readableResponse["trips"]["data"]["airport"]
		cityList = readableResponse["trips"]["data"]["city"]
	except KeyError:
		print datetime.today(), "WARNING: There were no results found for your request. Payload:", payload
		sys.exit(3)

	# Parse the response from the Google API.
	for trip in readableResponse["trips"]["tripOption"]:
		for slices in trip["slice"]:
			for segment in slices["segment"]:
				resultsMessage += "------------------\n"
				carrierCode = segment["flight"]["carrier"]
				flightNumber = segment["flight"]["number"]
				for carrier in carrierList:
					if carrier["code"]  == carrierCode:
						carrierName = carrier["name"]
				resultsMessage += "Flight number: "+flightNumber+" Carrier: "+carrierName+" ("+carrierCode+")\n"
				for leg in segment["leg"]:
					# Get all the NAMES of the airports that we need from our list of airport CODES.
					for airport in airportList:
						if leg["origin"] == airport["code"]:
							originAirportCity = airport["city"]
						if leg["destination"] == airport["code"]:
							destinationAirportCity = airport["city"]
						if origin1 == airport["code"]:
							subjectOriginAirportCity = airport["city"]
						if destination1 == airport["code"]:
							subjectDestinationAirportCity = airport["city"]
					# Get all the NAMES of the cities that we need from our list of city CODES.
					for city in cityList:
						if originAirportCity == city["code"]:
							originCity = city["name"]
						if destinationAirportCity == city["code"]:
							destinationCity = city["name"]
						if subjectOriginAirportCity == city["code"]:
							subjectOriginCity = city["name"]
						if subjectDestinationAirportCity == city["code"]:
							subjectDestinationCity = city["name"]
				resultsMessage += "Origin: "+originCity+" ("+leg["origin"]+") -> Destination: "+destinationCity+" ("+leg["destination"]+")"+"\n"
				resultsMessage += "Departure time: "+leg["departureTime"]+"\n"
				resultsMessage += "Arrival time: "+leg["arrivalTime"]+"\n"
		resultsMessage += "Total price: "+trip["saleTotal"]+"\n"
		resultsMessage += "__________________________________________\n"
	sendEmail(resultsMessage,subjectOriginCity,subjectDestinationCity,trip["saleTotal"])

if __name__ == "__main__":
	getArgs(sys.argv[1:])
