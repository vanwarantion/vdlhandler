#!/usr/bin/python

from pysqlite2 import dbapi2 as sqlite

conn = sqlite.connect('newcomers.db', detect_types=sqlite.PARSE_DECLTYPES)
cursor = conn.cursor()

#d = cursor.execute('SELECT log.id, log.filename, log.logsid, log.state logs.lookuptime FROM log AS i WHERE state<20 INNER JOIN logs as k ON (log.logsid=log.id)')
#~ d = cursor.execute('''
#~ SELECT i.id, i.filename, i.logsid, i.state, k.lookuptime
#~ FROM log AS i 
#~ WHERE i.state<20
#~ INNER JOIN logs as k
#~ ON k.id=i.logsid
#~ ''')
d = cursor.execute('SELECT i.id, i.filename, i.logsid, i.state, k.lookuptime FROM log AS i INNER JOIN logs as k ON (k.id=i.logsid) AND (i.id<20)')

rs = d.fetchall()

for i in rs:
    print i

