#!/usr/bin/python
'''

 Copyright (C) Alan Verdugo.

 Description:
	This program will use the Google QPX API to look for airplane tickets which 
	match certain criteria.

 Usage:
	python qpx.py [-h] -o ORIGIN -d DESTINATION [-D DURATION] [-t DELAY]
        [-s SOLUTIONS] [-a ADULTS] -P MAXPRICE
	Example:
		python qpx.py --origin GDL --destination CUU --duration 30 --delay 30
		--solutions 3 --adult 1 --maxPrice USD55000

 Arguments:
  -h, --help            show this help message and exit
  -o ORIGIN, --origin ORIGIN
                        Origin IATA airport code.
  -d DESTINATION, --destination DESTINATION
                        Destination IATA airport code.
  -D DURATION, --duration DURATION
                        The duration in days of the travel (for round trips).
                        Default is 7.
  -t DELAY, --delay DELAY
                        Number of days in the future to start searching for
                        trips (highly recommended).
  -s SOLUTIONS, --solutions SOLUTIONS
                        Maximum number of solutions that the program will
                        attempt to find. Default is 3.
  -a ADULTS, --adults ADULTS
                        Number of adult passengers for the trip.
  -P MAXPRICE, --maxprice MAXPRICE
                        The maximum allowed total price for the entire travel.

 Author:
	Alan Verdugo (alan@kippel.net)

 Creation date:
	2016-01-01 (?)

 Revision history:
	Author:		Date:		Notes:
	Alan		2016-06-08	Added this header.
	Alan        2016-06-11	Separated everything into functions.
	Alan		2016-08-11	Replaced getopt with argparse.
'''

import requests							# To get results from QPX.
import json
import sys
from email.mime.text import MIMEText	# Some email modules we'll need.
import smtplib							# For the actual email sending.
from datetime import date, datetime, timedelta  # Date handling
import argparse  # To get arguments from CLI.


APIKEY = "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
google_url = "https://www.googleapis.com/qpxExpress/v1/trips/search?key="+APIKEY
headers = {'content-type': 'application/json'}
qpx_home = "/opt/qpx/"
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
# TODO: Add a try statement here and move it to sendEmail()
emailFile = open(qpx_home + "mailList.txt", "r+")	# Dist. list, one address per line.
emailTo = emailFile.readlines()
emailFile.close()  # Close file after reading the email recipients.


# Send email with results.
def sendEmail(resultsMessage,originCity,destinationCity,saleTotal):
	msg = MIMEText(resultsMessage,"plain")
	emailSubject = "Flights found: "+originCity+" to "+destinationCity+", "+destinationCity+" to "+originCity+" for "+saleTotal+" or less."
	msg["Subject"] = emailSubject
	s = smtplib.SMTP(smtpServer)
	s.sendmail(emailFrom, emailTo, msg.as_string())
	s.quit()


def get_args(argv):
	parser = argparse.ArgumentParser()
	parser.add_argument("-o","--origin",
						help = "Origin IATA airport code.",
						dest = "origin",
						required = True)
	parser.add_argument("-d","--destination",
						help = "Destination IATA airport code.",
						dest = "destination",
						required = True)
	parser.add_argument("-D","--duration",
						help = "The duration in days of the travel (for round trips). Default is 7.",
						dest = "duration",
						default = "7")
	parser.add_argument("-t","--delay",
						help = "Number of days in the future to start searching for trips (highly recommended).",
						dest = "delay",
						default = "0")
	parser.add_argument("-s","--solutions",
						help = "Maximum number of solutions that the program will attempt to find. Default is 3.",
						dest = "solutions",
						default = "3")
	parser.add_argument("-a","--adults",
						help = "Number of adult passengers for the trip.",
						dest = "adults",
						default = "1")
	parser.add_argument("-P","--maxprice",
						help = "The maximum allowed total price for the entire travel.",
						dest = "maxprice",
						required = True)
	args = parser.parse_args()
	main(args.origin, args.destination, args.duration, args.delay, args.solutions, args.adults, args.maxprice)


def main(origin1, destination1, duration, delay, solutions, adults, max_price):
	global resultsMessage
	date1 = date.today() + timedelta(days=int(delay))
	# Variables used for the return trip (in round trips, obviously).
	origin2 = destination1
	destination2 = origin1
	date2 = date1 + timedelta(days=int(duration))  # Return date is departure date plus duration of travel.

	# Form the payload according to the arguments or default values.
	payload = '{"request":{"passengers":{"adultCount":'+adults+'},"slice":[{"origin":"'+origin1+'","destination":"'+destination1+'","date":"'+str(date1)+'"},{"origin":"'+origin2+'","destination":"'+destination2+'","date":"'+str(date2)+'"}],"maxPrice":"'+max_price+'","solutions":'+solutions+'}}'

	response = requests.post(google_url, data=payload, headers=headers)

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
	get_args(sys.argv[1:])
