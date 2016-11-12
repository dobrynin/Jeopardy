import sqlite3
import re

conn = sqlite3.connect('jeopardyWeb.sqlite')
cur = conn.cursor()

print "Creating JSON output on jeopardy.js..."
howmany = int(raw_input("How many nodes? "))

cur.execute('''SELECT COUNT(cat1) AS inbound, old_rank, new_rank, id, category
    FROM Categories JOIN Links ON Categories.id = Links.cat2
    GROUP BY id ORDER BY new_rank DESC''')

fhand = open('jeopardy.js','w')
nodes = list()
maxrank = None
minrank = None
for row in cur :
    nodes.append(row)
    rank = row[2]
    if maxrank < rank or maxrank is None : maxrank = rank
    if minrank > rank or minrank is None : minrank = rank
    if len(nodes) > howmany : break

if maxrank == minrank or maxrank is None or minrank is None:
    print "Error - please run jeopardyRank.py to compute page rank"
    quit()

fhand.write('jeopardyJSON = {"nodes":[\n')
count = 0
map = dict()
ranks = dict()
for row in nodes :
    if count > 0 : fhand.write(',\n')
    # print row
    rank = row[2]
    rank = 19 * ( (rank - minrank) / (maxrank - minrank) )
    fhand.write('{'+'"weight":'+str(row[0])+',"rank":'+str(rank)+',')
    fhand.write(' "id":'+str(row[3])+', "category":"'+re.escape(row[4].encode('utf-8'))+'"}')
    map[row[3]] = count
    ranks[row[3]] = rank
    count = count + 1
fhand.write('],\n')

cur.execute('''SELECT DISTINCT cat1, cat2 FROM Links''')
fhand.write('"links":[\n')

count = 0
for row in cur :
    # print row
    if row[0] not in map or row[1] not in map : continue
    if count > 0 : fhand.write(',\n')
    rank = ranks[row[0]]
    srank = 19 * ( (rank - minrank) / (maxrank - minrank) ) 
    fhand.write('{"source":'+str(map[row[0]])+',"target":'+str(map[row[1]])+',"value":3}')
    count = count + 1
fhand.write(']};')
fhand.close()
cur.close()

print "Open force.html in a browser to view the visualization"
