import sqlite3

conn = sqlite3.connect('jeopardyWeb.sqlite')
cur = conn.cursor()

# Find the ids that send out page rank - we only are interested
# in pages in the SCC that have in and out links
cur.execute('''SELECT DISTINCT cat1 FROM Links''')
firstWords = list()
for row in cur: 
    firstWords.append(row[0])

# Find the ids that receive page rank 
secondWords = list()
links = list()
cur.execute('''SELECT DISTINCT cat1, cat2 FROM Links''')
for row in cur:
    firstWord = row[0]
    secondWord = row[1]
    if firstWord == secondWord : continue
    if firstWord not in firstWords : continue
    if secondWord not in firstWords : continue
    links.append(row)
    if secondWord not in secondWords : secondWords.append(secondWord)

# Get latest page ranks for strongly connected component
prev_ranks = dict()
for node in firstWords:
    cur.execute('''SELECT new_rank FROM Categories WHERE id = ?''', (node, ))
    row = cur.fetchone()
    prev_ranks[node] = row[0]
    

sval = raw_input('How many iterations:')
many = 1
if ( len(sval) > 0 ) : many = int(sval)

# Sanity check
if len(prev_ranks) < 1 : 
    print "Nothing to page rank.  Check data."
    quit()

# Lets do Page Rank in memory so it is really fast
for i in range(many):
    # print prev_ranks.items()[:5]
    next_ranks = dict();
    total = 0.0
    for (node, old_rank) in prev_ranks.items():
        total = total + old_rank
        next_ranks[node] = 0.0
    # print total

    # Find the number of outbound links and sent the page rank down each
    for (node, old_rank) in prev_ranks.items():
        # print node, old_rank
        give_ids = list()
        for (firstWord, secondWord) in links:
            if firstWord != node : continue
           #  print '   ',firstWord,secondWord

            if secondWord not in secondWords: continue
            give_ids.append(secondWord)
        if ( len(give_ids) < 1 ) : continue
        amount = old_rank / len(give_ids)
        # print node, old_rank,amount, give_ids
    
        for id in give_ids:
            next_ranks[id] = next_ranks[id] + amount
    
    newtot = 0
    for (node, next_rank) in next_ranks.items():
        newtot = newtot + next_rank
    evap = (total - newtot) / len(next_ranks)

    # print newtot, evap
    for node in next_ranks:
        next_ranks[node] = next_ranks[node] + evap

    newtot = 0
    for (node, next_rank) in next_ranks.items():
        newtot = newtot + next_rank

    # Compute the per-page average change from old rank to new rank
    # As indication of convergence of the algorithm
    totdiff = 0
    for (node, old_rank) in prev_ranks.items():
        new_rank = next_ranks[node]
        diff = abs(old_rank-new_rank)
        totdiff = totdiff + diff

    avediff = totdiff / len(prev_ranks)
    print i+1, avediff

    # rotate
    prev_ranks = next_ranks

# Put the final ranks back into the database
print next_ranks.items()[:5]
cur.execute('''UPDATE Categories SET old_rank=new_rank''')
conn.commit()
for (id, new_rank) in next_ranks.items() :
    cur.execute('''UPDATE Categories SET new_rank=? WHERE id=?''', (new_rank, id))
conn.commit()
cur.close()

