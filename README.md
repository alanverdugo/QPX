# QPX

## A note regarding the Google QPX API
On April 10th, 2018, Google decided to stop supporting the QPX API. There is no good replacement for it and because of that, this program is unable to comsume the appropiate travel data, rendering it useless. I will keep the code here as it is, for documentation purposes and for reference in other projects.

## What does it do?
This is a program that uses the QPX Google API in order to look for flights according to your specifications. It is pretty simple, but it served two main purposes: 1) Made me practice and improve my Python skills. 2) Allowed me to setup a search and let it run indifinively, until certain condition are met. When these conditions are met, the program would alert me so I can quickly book those sweet cheap tickets. I want to travel cheaply but still not wasting my time looking at those offers sites. I am a programmer, I do not want to waste my time if a computer can do the job for me.
In other words, this program can be used to looks for cheap flights. You provide the criteria (number of passengers, origin and destination airport, price, etc.) and the program will start looking for matches, if and when it finds a match, the program will send an email with the details.
Does it work? Yes, once it is properly configured, it works extremelly well. It already saved me a lot of money by finding a cheap flight to Tokyo, and to this day it is still sending me alerts about cheap flights.

## How can I use it?
First of all, I am aware that this project is not very user friendly (that should change later). It is not a web or mobile application. For now, it is just a script that will send emails to you when your conditions are met. It can be very useful, but for now you will have to do some things in order to use it. The following is the basic usage:

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
                        The max total price for the entire travel. Preceded by currency code (USD, MXN, etc)

## Requirements.
- A valid QPX API key.
- Python 2.7
- Python modules:
  - requests
  - json
  - sys
  - email
  - smtplib
  - datetime
  - argparse

## Limitations.
There are some important limitations with the code (which I am trying to solve) and, more importantly, with the QPX API (which only Google itself could (but will unlikely) fix).
-  For one, the API does not allow searches for ranges of dates. For example, you cannot search for "a one-way trip during next month or so", or "a round trip that begins tomorrow and ends around December". No, we have to provide specific dates for departure every single flight we desire. Once you think about this, it becames obvious that this is a understandable but still huge limitation. There are, however, some workarounds.
-  As of the writting of this README file, Google only allows 50 free searches per day. They will start charging you when you do your 51st in a 24-hour period. If you are using this program for your own personal needs, 50 searches probably are more than enough, but you cannot expect to run millions of searches and expect them to be free.
-  Not all airlines are listed. This one requires some explanation: I learned that there are a lot of airlines in the world, and not all of them offer their data publicly. Most of the small (and cheap) airlines do not offer their data in APIs like QPX. Apparently, to get that data, you need to be listed as a travel-booking company and sacrifice a virgin unicorn to the elder gods. **What this means is that the results retrieved by the QPX API (and in turn, this program) will likely only include larger airlines, and for this reason, it is best used by looking for international trips.**
