#!/usr/bin/env python
# coding: utf-8

import os
import sys
import ConfigParser
import mysql.connector
import csv
from datetime import datetime
from progressbar import ProgressBar, Bar, Timer, SimpleProgress, ReverseBar
from colorama import Fore, Back, Style

currentDir = os.path.dirname(os.path.realpath(__file__))
stats = {
    'SUCCESS': 0,
    'EXIST': 0,
    'ERROR': 0
}

# Check argument
try:
    arg1 = sys.argv[1]
except IndexError:
    print "Usage: import.py <EXPORTING_CSV_FROM_OOKLA_REPORTING_INTERFACE>"
    print "Exmaple: import.py global.csv"
    exit(1)

# Check config
try:
    Config = ConfigParser.ConfigParser()
    Config.read(currentDir + '/config.ini')
except ConfigParser.Error as err:
    print err
    print "Unable to read configuration file, exist ? Have right permissions ?"
    exit(2)

# Check mysql connection
try:
    cnx = mysql.connector.connect(host=Config.get('mysql', 'host'),
                                  user=Config.get('mysql', 'user'),
                                  password=Config.get('mysql', 'password'),
                                  database=Config.get('mysql', 'database'),
                                  unix_socket=Config.get('mysql', 'socket'),
                                  port=Config.get('mysql', 'port')
                                  )
    cursor = cnx.cursor()
except (mysql.connector.Error, ConfigParser.Error) as err:
    print "Connection with mysql error: %s" % err
    exit(3)

# Main program
numLines = sum(1 for line in open(sys.argv[1], 'r'))
widgets = [Bar('>'), ' ', Timer(), ' ', '(', SimpleProgress(), ')', ' ', ReverseBar('<')]
pbar = ProgressBar(widgets=widgets, maxval=numLines).start()
with open(sys.argv[1], 'r') as csvFile:
    reader = csv.DictReader(csvFile, delimiter=',')
    for entry in reader:
        # Update progress bar
        pbar.update(reader.line_num)
        # Transform given date to real datetime
        convertedDate = datetime.strptime(entry['TEST_DATE'], '%m/%d/%Y %H:%M:%S %Z')
        # Format for mysql datetime
        entry['TEST_DATE'] = convertedDate.strftime('%Y-%m-%d %H:%M:%S')

        keys = '(' + ','.join(entry.keys()) + ')'
        values = tuple(entry.values())
        sql = "INSERT INTO results %s VALUES %s" % (keys, values)

        # Send formated query
        try:
            cursor.execute(sql)
            cnx.commit()
            stats['SUCCESS'] += 1
        except mysql.connector.Error as err:
            if err.errno == 1062:
                stats['EXIST'] += 1
            else:
                stats['ERROR'] += 1
                # print("Error: {}".format(err))

cnx.close()
pbar.finish()
total = str(stats['SUCCESS'] + stats['ERROR'] + stats['EXIST'])
print
print Fore.LIGHTCYAN_EX + "Summary: " \
      + Fore.RED + str(stats['ERROR']) + " errors" \
      + Fore.LIGHTCYAN_EX + ", " \
      + Fore.YELLOW + str(stats['EXIST']) + " already exists (not duplicate)" \
      + Fore.LIGHTCYAN_EX + ", " \
      + Fore.GREEN + str(stats['SUCCESS']) + " success" \
      + Fore.LIGHTCYAN_EX + "  (" + str(stats['SUCCESS']) + "/" + total + ")" \
      + Style.RESET_ALL + Fore.RESET
