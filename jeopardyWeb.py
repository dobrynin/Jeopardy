import sqlite3
import urllib
import ssl 
from urlparse import urljoin
from urlparse import urlparse
from bs4 import BeautifulSoup
import re

# banned words are insignificant words that we do not want to analyze
bannedWords = ['A','IN','THE','OF','I','PUT','YOU','ON', 'IT\'S', 'ALL', 'TO', 'ME','IS','FOR','BY','THAT','DON\'T','IF','IT','THEY','WILL','YOUR']

# data source
dataConn = sqlite3.connect('jeopardy.sqlite')
# new database with connections between categories
linksConn = sqlite3.connect('jeopardyWeb.sqlite')
dataCur = dataConn.cursor()
linksCur = linksConn.cursor()

linksCur.execute('''CREATE TABLE IF NOT EXISTS Categories
	(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, category TEXT UNIQUE, old_rank FLOAT, new_rank FLOAT)''')
	
linksCur.execute('''CREATE TABLE IF NOT EXISTS Links 
    (cat1 INTEGER, cat2 INTEGER)''')

catDict = {} # dictionary with categories as keys and individual words as values
try:
	dataCur.execute('SELECT id, category FROM Categories')
except:
	print 'Database error. Check data.'
for row in dataCur:
	category = row[1]
	words = re.findall(ur"[\w']+",category,re.UNICODE) # find words
	catDict[row[0]] = words
	linksCur.execute('INSERT OR IGNORE INTO Categories (category, old_rank, new_rank) VALUES ( ?, ?, ? )', ( category, 1, 1 ) ) 
linksConn.commit()

connections = []
for cat1 in catDict:
	for cat2 in catDict:
		if cat1 == cat2: # don't want words to connect to themselves if they are repeated in a category name
			continue
		for word in catDict[cat1]:
			if word in bannedWords:
				continue
			if word in catDict[cat2]: # checks if there is a common word connection between two categories
				if [cat1, cat2] in connections: # if connection already exists, don't repeat
					continue
				connections.append([cat1, cat2]) # keep a record in memory of existing connections
				linksCur.execute('INSERT OR IGNORE INTO Links (cat1, cat2) VALUES ( ?, ? )', ( cat1, cat2 ) ) 
linksConn.commit()
dataCur.close()
linksCur.close()

