import sqlite3
import urllib
from bs4 import BeautifulSoup
import re
import codecs

# escape sequences for converting unicode
ESCAPE_SEQUENCE_RE = re.compile(r'''
    ( \\U........      # 8-digit hex escapes
    | \\u....          # 4-digit hex escapes
    | \\x..            # 2-digit hex escapes
    | \\[0-7]{1,3}     # Octal escapes
    | \\N\{[^}]+\}     # Unicode characters by name
    | \\[\\'"abfnrtv]  # Single-character escapes
    )''', re.UNICODE | re.VERBOSE)


# function for converting unicode 
def decode_escapes(s):
    def decode_match(match):
        return codecs.decode(match.group(0), 'unicode-escape')

    return ESCAPE_SEQUENCE_RE.sub(decode_match, s)

# create and/or connect to database
conn = sqlite3.connect('jeopardy.sqlite')
cur = conn.cursor()

# Create database tables
cur.execute('''CREATE TABLE IF NOT EXISTS Clues
(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, clue VARCHAR, category_id INT, clue_value_id TINYINT, correct_response VARCHAR, round_id TINYINT,
show_number_id SMALLINT, UNIQUE( clue, show_number_id ))''')

cur.execute('''CREATE TABLE IF NOT EXISTS Categories
(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, category VARCHAR UNIQUE)''')

cur.execute('''CREATE TABLE IF NOT EXISTS Clue_Values
(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, clue_value SMALLINT UNIQUE)''')

cur.execute('''CREATE TABLE IF NOT EXISTS Rounds
(id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE, round VARCHAR UNIQUE)''')

cur.execute('''CREATE TABLE IF NOT EXISTS Show_Numbers
(id INTEGER NOT NULL PRIMARY KEY UNIQUE, show_number VARCHAR UNIQUE, air_date SMALLDATETIME)''')

# determine start and end games
cur.execute('SELECT max(id) FROM Show_Numbers')
while True:
	try:
		start = int(raw_input('Enter first game ID to retrieve: '))
		break
	except:
		continue
row = cur.fetchone()
if row[0] is not None and row[0] > start: 
	start = row[0] # don't waste time on already processed games
	
end = int(raw_input('Enter last game ID to retrieve: ')) + 1
	
# provide base url and range of game IDs to iterate through
serviceurl = 'http://www.j-archive.com/showgame.php?game_id='
game_ids = range(start,end)

# Rounds will always be the same
rounds = ['Jeopardy! Round','Double Jeopardy! Round','Final Jeopardy! Round'] # for use in database
roundVars = ['jeopardy_round', 'double_jeopardy_round'] # for parsing html. Final Jeopardy! is treated seperately due to html formatting differences.

# iterate through games
for game_id in game_ids:
		
	# status update
	print 'Retrieving Game ID:',game_id
	
	# construct url
	url = serviceurl + str(game_id)
	html = urllib.urlopen(url).read()
	soup = BeautifulSoup(html, "html5lib")

	titleTag = soup.title.contents[0]
	# obtain show number and air date using regural expression search
	show_number = re.findall('\-\s(.+)\,',titleTag)[0]
	air_date = re.findall('[\-0-9]{10}$',titleTag)[0]

	clues = []
	roundIndex = 0
	# iterate through Jeopardy! and Double Jeopardy!
	for round in roundVars:
		
		# html for current round
		jeopardy_roundTag = soup.find('div', id=round)
		if not jeopardy_roundTag: # some games lack data
			continue
		# obtain category name html tags
		category_names = jeopardy_roundTag.find_all('td', class_="category_name")

		# obtain category names
		categories = []
		for category_name in category_names:
			category = ''
			# sometimes category names are split up into multiple strings for formatting reasons. This catches that.
			categoryStrings = category_name.strings
			for categoryString in categoryStrings:
				category += categoryString
			category = category.replace(u"\u2019", "'") # a few categories have a non-typical apostrophe character which must be converted
			categories.append(category)
		
		# html tags for each row in the html data round table
		tableRowTags = jeopardy_roundTag.find_all('tr')
		for tableRowTag in tableRowTags:
			# obtain html clue tags
			clueTags = tableRowTag.find_all('td', class_='clue')
			# skip rows without clues
			if not clueTags:
				continue
			
			# vector of clue dictionaries
			clueVec = []
			for clueTag in clueTags:
				# every clue is a dictionary with all other parameters as keys
				clueDict = {}
				# initialize clue text variable
				clue = ''
				try:
					# obtain clue text. Sometimes split into multiple strings for html formatting reasons. This catches that.
					clueStrings = clueTag.find('td', class_="clue_text").strings
					for clueString in clueStrings:
						clue += clueString
					clue = clue.replace(u"\u2019", "'")
					try:
						# obtain clue value
						clue_value = clueTag.find('td', class_="clue_value").contents[0]
					except:
						# some clues are daily doubles with contestant-determined values
						clue_value = clueTag.find('td', class_="clue_value_daily_double").contents[0]
					clueDict['clue'] = clue
					clueDict['clue_value'] = clue_value
					clueDict['round'] = rounds[roundIndex]
					clueDict['show_number'] = show_number
					clueDict['air_date'] = air_date
					
					# obtain string of html correct_response tag
					divTag = clueTag.find(onmouseover=True)
					onmouseoverTag = divTag['onmouseover']
					onmouseoverSoup = BeautifulSoup(onmouseoverTag,"html5lib")
					correctResponseFragments = onmouseoverSoup.find('em').strings
					correct_response = ''
					for correctResponseFragment in correctResponseFragments:
						correct_response += correctResponseFragment
					correct_response = correct_response.replace(u"\u2019", "'")
					clueDict['correct_response'] = decode_escapes(correct_response)
					
					clueVec.append(clueDict)
					

				except:
					# some clues are never revealed and are thus empty. Leave spot in vector in empty with ''.
					clueVec.append('')
			
			# categories are handled differently because they are not directly associated with clues in the html.
			for i in range(len(categories)):
				if clueVec[i]:
					clueVec[i]['category'] = categories[i]
				else:
					continue
			
			for clue in clueVec:
				clues.append(clue)
			
			
		roundIndex = roundIndex + 1

	# Final Jeopardy! Round
	clueDict = {}
	jeopardy_roundTag = soup.find('div', id='final_jeopardy_round')
	if jeopardy_roundTag:
		category_name = jeopardy_roundTag.find('td', class_="category_name")
		# sometimes category names are split up into multiple strings for formatting reasons. This catches that.
		categoryStrings = category_name.strings
		category = ''
		for categoryString in categoryStrings:
			category += categoryString
		clue = jeopardy_roundTag.find('td', class_='clue_text').contents[0]
		clue = clue.replace(u"\u2019", "'")
		clue_value = None
		
		# obtain string of html correct_response tag
		divTag = jeopardy_roundTag.find(onmouseover=True)
		onmouseoverTag = divTag['onmouseover']
		onmouseoverSoup = BeautifulSoup(onmouseoverTag,"html5lib")
		correctResponseFragments = onmouseoverSoup.find('em').strings
		correct_response = ''
		for correctResponseFragment in correctResponseFragments:
			correct_response += correctResponseFragment
		correct_response = correct_response.replace(u"\u2019", "'")

		clueDict['clue'] = clue
		clueDict['clue_value'] = clue_value
		clueDict['round'] = rounds[roundIndex]
		clueDict['show_number'] = show_number
		clueDict['air_date'] = air_date
		clueDict['correct_response'] = decode_escapes(correct_response)
		category = category.replace(u"\u2019", "'")
		clueDict['category'] = category
		clues.append(clueDict)

		
	# insert each clue's data into database
	for clue in clues:
		if clue:
			cur.execute('SELECT id FROM Show_Numbers WHERE show_number = ? LIMIT 1', (clue['show_number'], ) )
			try:
				show_number_id = cur.fetchone()[0]
			except:
				cur.execute('INSERT OR IGNORE INTO Show_Numbers (id, show_number, air_date) VALUES ( ?, ?, ? )', (game_id, show_number, air_date) )
				conn.commit()
				show_number_id = cur.lastrowid
							
			cur.execute('SELECT id FROM Rounds WHERE round = ? LIMIT 1', (clue['round'], ) )
			try:
				round_id = cur.fetchone()[0]
			except:
				cur.execute('INSERT OR IGNORE INTO Rounds (round) VALUES ( ? )', (clue['round'], ) )
				conn.commit()
				round_id = cur.lastrowid				
			
			cur.execute('SELECT id FROM Clue_Values WHERE clue_value = ? LIMIT 1', (clue['clue_value'], ) )
			try:
				clue_value_id = cur.fetchone()[0]
			except:
				cur.execute('INSERT OR IGNORE INTO Clue_Values (clue_value) VALUES ( ? )', (clue['clue_value'], ) )
				conn.commit()
				clue_value_id = cur.lastrowid

			cur.execute('SELECT id FROM Categories WHERE category = ? LIMIT 1', (clue['category'], ) )
			try:
				category_id = cur.fetchone()[0]
			except:
				cur.execute('INSERT OR IGNORE INTO Categories (category) VALUES ( ? )', (clue['category'], ) )
				conn.commit()
				category_id = cur.lastrowid				
			
			cur.execute('INSERT OR IGNORE INTO Clues (clue, category_id, clue_value_id, correct_response, round_id, show_number_id) VALUES ( ?, ?, ?, ?, ?, ?)',
				( clue['clue'], category_id, clue_value_id, clue['correct_response'], round_id, show_number_id) )
			conn.commit()

cur.close()
