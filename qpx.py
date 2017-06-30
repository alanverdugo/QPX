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
                        The max total price for the entire travel. Preceded by 
                        currency code (USD, MXN, etc)

 Author:
    Alan Verdugo (alan@kippel.net)

 Creation date:
    2016-01-01 (?)

 Revision history:
    Author:     Date:       Notes:
    Alan        2016-06-08  Added this header.
    Alan        2016-06-11  Separated everything into functions.
    Alan        2016-08-11  Replaced getopt with argparse.
    Alan        2016-08-16  Improved the send_email function.
    Alan        2016-08-21  Now we read config values from an external file.
    Alan        2017-05-13  Changed indentation to spaces.
                            Added some readability improvements.
                            Fixed one-way trip process.
    Alan        2017-05-23  Added the -x/--date option, which allows to look 
                            for specific dates.
    Alan        2017-06-30  Minor improvements
'''

# Mainly for path handling.
import os

# Return code management.
import sys

# JSON parsing.
import json

# Email functionality.
import smtplib

# To get results from QPX.
import requests

# To get arguments from CLI.
import argparse

# Some email modules we'll need.
from email.mime.text import MIMEText

# Date handling.
from datetime import date, datetime, timedelta

# Log management.
import logging


results_message = []
results_message_string = ""
global destination_city
global origin_city
global subject_destination_city
global subject_origin_city
subject_destination_city = ""
subject_origin_city = ""
subject_origin_airport_city = ""
subject_destination_airport_city = ""

# Configuration file.
config_file = os.path.join("/opt", "qpx", "config.json")

# Request headers.
headers = {'content-type': 'application/json'}


def read_config():
    # Open the config JSON file.
    try:
        config = open(config_file,"r+")
        readable_config = json.load(config)
        config.close()
    except Exception as exception:
        print "ERROR: Unable to read configuration file.", config_file, exception
        sys.exit(1)
    # TODO: Validate that the JSON config is in a valid JSON format.
    # Assign the configuration values to global variables.
    global email_from
    global smtp_server
    global email_to
    global qpx_home
    global google_url
    email_from = readable_config["notification"]["sender"]
    smtp_server = readable_config["notification"]["SMTP_server"]
    email_to = readable_config["notification"]["recipients"]["email"]
    qpx_home = readable_config["home"]
    # Concatenate the Google QPX API base URL with my API key.
    google_url = readable_config["QPX_URL"] + readable_config["API_KEY"]


# TODO: Sent others kind of notifications (SMS?, Whatsapp?, Telegram?, A page?)


# Send email with results.
def send_email(results_message, origin_city, destination_city, sale_total):
    msg = MIMEText(results_message,"plain")
    email_subject = "Flights found: {0} to {1} for {2} or "\
    	"less".format(destination_city, origin_city, sale_total)
    msg["subject_"] = email_subject
    s = smtplib.SMTP(smtp_server)
    try:
        s.sendmail(email_from, email_to, msg.as_string())
        s.quit()
    except Exception as exception:
        print "ERROR: Unable to send notification email.", exception
        sys.exit(1)
    else:
    	print "INFO: Success! Notification email sent to:", email_to
    	print "Message:", results_message
    	sys.exit(0)


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
    parser.add_argument("-x","--date",
        help = "Departure date in YYYY-MM-DD",
        dest = "date",
        default = False,
        required = False)
    parser.add_argument("-D","--duration",
        help = "The duration in days of the travel (for round trips)."\
        	"Default is 7.",
        dest = "duration",
        default = False,
        required = False)
    parser.add_argument("-t","--delay",
        help = "Number of days in the future to start searching for trips "\
        	"(highly recommended).",
        dest = "delay",
        default = "0")
    parser.add_argument("-s","--solutions",
        help = "Maximum number of solutions that the program will attempt to "\
        	"find. Default is 3.",
        dest = "solutions",
        default = "3")
    parser.add_argument("-a","--adults",
        help = "Number of adult passengers for the trip.",
        dest = "adults",
        default = "1")
    parser.add_argument("-P","--maxprice",
        help = "The max total price for the entire travel. Preceded by "\
        	"currency code (USD, MXN, etc)",
        dest = "maxprice",
        required = True)
    args = parser.parse_args()
    main(args.origin, args.destination, args.date, args.duration, args.delay, 
    	args.solutions, args.adults, args.maxprice)


def main(origin1, destination1, mydate, duration, delay, solutions, adults, 
	max_price):
    global results_message

    if mydate:
        # If an specific date was supplied, use it.
        date1 = mydate
    else:
        # If an specific travel date was not provided, use only the delay 
        # days counting from today().
        date1 = date.today() + timedelta(days=int(delay))

    # If we are searching for a round trip...
    if duration:
        # Variables used for the return trip.
        origin2 = destination1
        destination2 = origin1
        # Return date is departure date plus duration of travel.
        date2 = date1 + timedelta(days=int(duration))
        # Form the payload according to the arguments or default values.
        payload = '{"request":{"passengers":{"adultCount":'+adults+'},"slice":[{"origin":"'+origin1+'","destination":"'+destination1+'","date":"'+str(date1)+'"},{"origin":"'+origin2+'","destination":"'+destination2+'","date":"'+str(date2)+'"}],"maxPrice":"'+max_price+'","solutions":'+solutions+'}}'
    else:
        # In case we are searching for a 1-way trip, the request will be formed
        # differently.
        payload = '{"request":{"passengers":{"adultCount":'+adults+'},"slice":[{"origin":"'+origin1+'","destination":"'+destination1+'","date":"'+str(date1)+'"}],"maxPrice":"'+max_price+'","solutions":'+solutions+'}}'

    try:
        response = requests.post(google_url, data=payload, headers=headers)
    except Exception as exception:
        print "FATAL ERROR: Unable to execute request.", exception
        sys.exit(1)

    # The status code should be 200 (success). Catch anything else and handle.
    if response.status_code != 200:
        print "FATAL ERROR: The response status code is:", response.status_code, response.reason
        sys.exit(1)

    # Check if we don't have an empty result set.
    try:
        readable_response = response.json()
    except ValueError:
        print datetime.today(), "ERROR: Empty result set. Payload:", payload
        sys.exit(2)

    # Check if there were no travel options returned.
    try:
        carrier_list = readable_response["trips"]["data"]["carrier"]
        airport_list = readable_response["trips"]["data"]["airport"]
        city_list = readable_response["trips"]["data"]["city"]
    except KeyError:
        print datetime.today(), "WARNING: There were no results found for "\
        	"your request. Payload:", payload
        sys.exit(3)

    # Parse the response from the Google API.
    for trip in readable_response["trips"]["tripOption"]:
        for slices in trip["slice"]:
            for segment in slices["segment"]:
                results_message.append("------------------")
                carrier_code = segment["flight"]["carrier"]
                flight_number = segment["flight"]["number"]
                for carrier in carrier_list:
                    if carrier["code"]  == carrier_code:
                        carrier_name = carrier["name"]
                results_message.append("Flight number: "+flight_number+" Carrier: "+carrier_name+" ("+carrier_code+")")
                for leg in segment["leg"]:
                    # Get all the NAMES of the airports that we need from 
                    # our list of airport CODES.
                    for airport in airport_list:
                        if leg["origin"] == airport["code"]:
                            origin_airport_city = airport["city"]
                        if leg["destination"] == airport["code"]:
                            destination_airport_city = airport["city"]
                        if origin1 == airport["code"]:
                            subject_origin_airport_city = airport["city"]
                        if destination1 == airport["code"]:
                            subject_destination_airport_city = airport["city"]
                    # Get all the NAMES of the cities that we need from 
                    # our list of city CODES.
                    for city in city_list:
                        if origin_airport_city == city["code"]:
                            origin_city = city["name"]
                        if destination_airport_city == city["code"]:
                            destination_city = city["name"]
                        if subject_origin_airport_city == city["code"]:
                            subject_origin_city = city["name"]
                        if subject_destination_airport_city == city["code"]:
                            subject_destination_city = city["name"]
                results_message.append("Origin: "+origin_city+" ("+leg["origin"]+") -> Destination: "+destination_city+" ("+leg["destination"]+")")
                results_message.append("Departure time: "+leg["departureTime"])
                results_message.append("Arrival time: "+leg["arrivalTime"])
        results_message.append("Total price: "+trip["saleTotal"])
        results_message.append("__________________________________________")

        # Concatenate the list of result messages into a single string.
        results_message_string = "\n".join(results_message)

    send_email(results_message_string, subject_origin_city, 
    	subject_destination_city, trip["saleTotal"])


if __name__ == "__main__":
    # Read configuration values from external config file.
    read_config()
    # Parse arguments from the CLI.
    get_args(sys.argv[1:])
