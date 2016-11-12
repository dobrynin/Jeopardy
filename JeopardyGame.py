import sqlite3
import re

print '\nWelcome to Jeopardy!\nEnter "quit" to exit program\n'
conn = sqlite3.connect('jeopardy.sqlite')
cur = conn.cursor()
score = 0 # initialize score of player
print 'Score: $' + str(score) + '\n'
while True:
	cur.execute('''SELECT clue, correct_response, category, clue_value, round, show_number FROM Clues
		JOIN Categories ON Clues.category_id = Categories.id
		JOIN Clue_Values on Clues.clue_value_id = Clue_Values.id
		JOIN Rounds on Clues.round_id = Rounds.id
		JOIN Show_Numbers ON Clues.show_number_id = Show_Numbers.id
		ORDER BY RANDOM() LIMIT 1''')
		
	cluedata = cur.fetchone()
	clue = cluedata[0].encode('utf8')
	correct_response = cluedata[1].encode('utf8')
	re.sub('\(.*?\)','',correct_response)
	correct_response.strip()
	lowercase_correct_response = correct_response.lower()
	category = cluedata[2].encode('utf8')
	while True:
		if cluedata[3]:
			clue_value_string = cluedata[3].encode('utf8')
		else:
			print 'Final Jeopardy! Question'
			clue_value_string = raw_input('Enter wager: ')
		if '$' in clue_value_string:
			sign_location = clue_value_string.find('$')
			clue_value = clue_value_string[sign_location+1:]
		else:
			clue_value = clue_value_string
		clue_value = clue_value.replace(',','')
		try:
			int(clue_value)
			break
		except:
			continue
	print 'Category:',category
	print 'Clue Value:',clue_value_string
	print 'Clue:',clue,'\n'	

	response = raw_input('>')
	if response == 'quit':
		break
	if response.lower().strip() == lowercase_correct_response:
		print 'Correct!'
		score += int(clue_value)
		print 'Score: $' + str(score) + '\n'
	else:
		print 'Incorrect.'
		print 'Correct Response:',correct_response
		score -= int(clue_value)
		print 'Score: $' + str(score) + '\n'
cur.close()