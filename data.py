#!/usr/bin/python
# -*- coding: utf-8 -*-

# TODO: Assign status to logged files (0:found, 10:executed, 20:lost, 30:moved)


# database and settings
# dependencies: python-pysqlite2

# change this to access another file:
defaultDbPath = 'newcomers.db'

# Database Interface Class:
class dbi:
    import datetime
    import time
    from pysqlite2 import dbapi2 as sqlite
    def __init__(self, filepath, defaultsXML = 'default.xml'):
        import os
        self.dbf = filepath
        dbdefaults = False
        if not os.path.isfile(self.dbf):
            dbdefaults = True
        self.logid = 0
        self.conn = self.sqlite.connect(self.dbf, detect_types=self.sqlite.PARSE_DECLTYPES)
        self.cursor = self.conn.cursor()
        self.checkdb()
        if dbdefaults == True:
            self.demotypes(self.importXML(defaultsXML))

    def demotypes(self, tofill):
        # insert types:
        for i in tofill['types']:
            self.cursor.execute('INSERT OR REPLACE INTO types VALUES (NULL, "%s")' % i['name'])
            i['id'] = self.cursor.lastrowid
            for j in i['patterns']:
                print "Adding type: ", j
                self.cursor.execute(r'INSERT OR REPLACE INTO typepatterns VALUES (NULL, "%s", %d)' % (j, i['id']))
        # insert regex
        filt = []
        for i in tofill['cats'].keys():
            print '\n', i, tofill['cats'][i]
            for j in tofill['cats'][i]['filter']:
                # for cat filters:
                for k in tofill['types']:
                    if k['name'] == j['type']:
                        j['typeid'] = k['id']
                        break
                # fill filters:
                if not j in filt:
                    filt.append(j)
                    self.cursor.execute(r'INSERT OR REPLACE INTO rgxpatterns VALUES (NULL, "%s")' % j['regex'])
                    j['rgxid'] = self.cursor.lastrowid
            # add cat:
            tofill['cats'][i]['atage'] = int(tofill['cats'][i]['atage'])
            if not ('action' in tofill['cats'][i]):
                tofill['cats'][i]['action'] = ''
            if not ('moveto' in tofill['cats'][i]):
                tofill['cats'][i]['moveto'] = ''
            if not ('priority' in tofill['cats'][i]):
                tofill['cats'][i]['priority'] = 0
            tofill['cats'][i]['priority'] = int(tofill['cats'][i]['priority'])
            self.cursor.execute('INSERT OR REPLACE INTO categories VALUES (NULL, "%s", "%s","%s", %d, %d)' % (i, tofill['cats'][i]['moveto'], tofill['cats'][i]['action'], tofill['cats'][i]['atage'], tofill['cats'][i]['priority']))
            tofill['cats'][i]['catid'] = self.cursor.lastrowid
            # add if tvshow
            if 'tvshow' in tofill['cats'][i]:
                self.cursor.execute(r'INSERT OR REPLACE INTO tvshows VALUES (%d, NULL, NULL, NULL)' % tofill['cats'][i]['catid'])
            # create filters
            for j in tofill['cats'][i]['filter']:
                self.cursor.execute('INSERT OR REPLACE INTO filters VALUES (%d, %d, %d)' % (j['typeid'], j['rgxid'], tofill['cats'][i]['catid']))
        #print 'filters:', filt
        
        self.conn.commit()
    
    def importXML(self, xmlpath):
        from lxml import etree as et
        self.etree = et
        # read xml as text file
        f = open(xmlpath, 'r')
        txt = f.read()
        # parse:
        root = self.etree.fromstring(txt)
        types = []
        for a in root.find("types"):
            t = {}
            t['name'] = a.items()[0][1]
            t['patterns'] = []
            for i in a:
                t['patterns'].append(i.text)
            types.append(t)
        # Categories:
        cats = {}
        for a in root.find("categories"):
            if a.tag == 'category':
                self.__parseCat(a, cats)
        return {'types': types, 'cats': cats}
        # print 
    
    def __parseCat(self, xmlpath, rv):
        c = {'filter': []}
        #print "Parsing Category:", xmlpath.items()[0][1]
        children = []
        for i in xmlpath:
            if i.tag in ['moveto', 'atage', 'action', 'priority']:
                c[i.tag] = i.text
            if i.tag == 'filter':
                cf = {}
                cf['type'] = i.items()[0][1]
                cf['regex'] = i.text
                c['filter'].append(cf)
            if i.tag == 'tvshow':
                c['tvshow'] = True
            if i.tag == 'category':
                children.append([i.items()[0][1], i])
        # import parent filters
        if len(children) > 0:
            #print "Has children:"
            for i in children:
                #print '\t', i[0]
                self.__parseCat(i[1], rv)
                for f in c['filter']:
                    rv[i[0]]['filter'].append(f)
        #print "Parsed:", c
        rv[xmlpath.items()[0][1]] = c
    
    
    def checkdb(self):
        # Create tables:
        # logs (lookup records): id, datetime
        # log (lookup results): id, filename, type, logsid
        # logtypes (logged file types): order, text, logid
        # types (filetypes): id, name, valid
        # typepatterns (filetype patterns): id, pattern, ftname ID
        # rgxpatterns (tvshow filename regex  patterns): id, pattern
        # categories (individual actions): id, name, moveto, atage(days)
        # filters (filters for categories): typeID, rgxID, catID
        # tv shows (identification for shows): catID, lastS, lastE
        
        self.cursor.execute("CREATE TABLE IF NOT EXISTS logs (id INTEGER PRIMARY KEY, lookuptime TIMESTAMP)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS log (id INTEGER PRIMARY KEY, filename TEXT, type TEXT, age TIMESTAMP, logsid NUMERIC, state INTEGER)")
        #self.cursor.execute("CREATE TABLE IF NOT EXISTS logtypes (ftorder NUMERIC, text TEXT, logid NUMERIC)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS types (id INTEGER PRIMARY KEY, name TEXT UNIQUE)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS typepatterns (id INTEGER PRIMARY KEY, pattern TEXT UNIQUE, typeID INTEGER)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS rgxpatterns (id INTEGER PRIMARY KEY, pattern TEXT UNIQUE)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS categories (id INTEGER PRIMARY KEY, name TEXT UNIQUE, moveto TEXT, exec TEXT, atage INTEGER, priority INTEGER)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS filters (typeID INTEGER, rgxID INTEGER, catID INTEGER)")
        self.cursor.execute("CREATE TABLE IF NOT EXISTS tvshows (catID INTEGER UNIQUE, lastS INTEGER, lastE INTEGER, lastLogID INTEGER)")
        
        self.conn.commit()
    
    def updateFilestat(self, fileid, newstat = 0):
        d = self.cursor.execute('UPDATE log SET state=%d WHERE id=%d' % (newstat, fileid))
        self.conn.commit()
    
    def updateShow(self, catID, cs = 0, ce = 0, logID = 0):
        # Updates or returns tvshow information:
        # check if we have that show:
        d = self.cursor.execute('SELECT lastS, lastE, lastLogID FROM tvshows WHERE catID =' + str(catID))
        rs = d.fetchone()
        if rs == None:
            # If not exists; insert one
            self.cursor.execute('INSERT OR REPLACE INTO tvshows VALUES (%d, %d, %d, %d)' % (catID, cs, ce, logID))
            return None
        else:
            # Update:
            print "rs: ", rs
            rv = {'season': rs[0], 'episode': rs[1], 'lastseenID': rs[2]}
            if rs[0] > cs:
                cs = rs[0]
            if rs[1] > ce:
                ce = rs[1]
            self.cursor.execute('UPDATE tvshows SET lastS=%d, lastE=%d, lastLogID=%d' % (cs, ce, logID))
            self.conn.commit()
            return rv
    
    def addfile(self, fname, typearr, fileage):
        # TODO: convert this to a queue for stack of files
        # TODO: only add new files
        # check logid:
        if self.logid == 0:
            # create if this is first record
            self.cursor.execute( 'INSERT INTO logs VALUES (?, ?)', (None, self.datetime.datetime.now()) )
            self.logid = self.cursor.lastrowid
            self.conn.commit()
        # write lookup results to the database
        # Check if entry exists:
        fa = self.datetime.datetime.fromtimestamp(self.time.mktime(self.time.gmtime(fileage)))
        d = self.cursor.execute('SELECT COUNT(id) FROM log WHERE filename="%s"' % (fname, fa))
        rs = d.fetchone()
        if rs[0] > 0:
            return 1
        # log entry
        self.cursor.execute('INSERT INTO log VALUES (?, ?, ?, ?, ?, 0)', (None, fname, typearr[0], fa, self.logid))
        sid = self.cursor.lastrowid
        # log details
        #~ for i in range(1, len(typearr)):
            #~ self.cursor.execute('INSERT INTO logtypes VALUES (%d, "%s", "%d")' % (i, typearr[i], sid))
        self.conn.commit()
        return 0
        
    
    def addftype(self, pattern, text, typeID = 0):
        if text == '':
            return None    # no tag given
        if typeID == 0:
            # new type
            self.cursor.execute('INSERT INTO types VALUES (null, "%s")' % (text))
            typeID = self.cursor.lastrowid
        self.cursor.execute('INSERT OR REPLACE INTO typepatterns VALUES (NULL, "%s", "%s")' % (pattern, typeID))
        self.conn.commit()
        return self.cursor.lastrowid
        
    def getLogage(self):
        # return time passed since last log
        d = self.cursor.execute('SELECT lookuptime FROM logs AS "[timestamp]" ORDER BY id DESC LIMIT 1')
        rs = d.fetchone()
        return rs[0]
        
    
        
    def getTypeid(self, pattern):
        d = self.cursor.execute('SELECT typeID FROM typepatterns WHERE pattern="' + pattern + '"')
        rs = d.fetchone()
        if rs:
            return rs[0]
        else:
            return None
    
    
    def getTypepatterns(self):
        d = self.cursor.execute('SELECT pattern, typeID FROM typepatterns')
        rs = d.fetchall()
        rv = {}
        if rs == None:
            return None
        else:
            for i in rs:
                rv[i[0]] = i[1]
            return rv
    
    def getCategories(self):
        # return categories from database
        d = self.cursor.execute('SELECT id, name, moveto, exec, atage, priority FROM categories')
        rs = d.fetchall()
        rv = []
        if rs == None:
            return None
        else:
            for i in rs:
                rv.append({'id': i[0], 'name': i[1], 'moveto': i[2], 'exec': i[3], 'atage': i[4], 'priority': i[5]})
            for i in rv:
                i['filters'] = self.getFilters(i['id'])
            return rv
    
    def getFilters(self, catID):
        d = self.cursor.execute('SELECT typeID, rgxID FROM filters WHERE "catID"=' + str(catID))
        rs = d.fetchall()
        rv = []
        if rs == None:
            return None
        else:
            for i in rs:
                rv.append([i[0], i[1]])
            return rv
    
    def getNamepatterns(self):
        d = self.cursor.execute('SELECT id, pattern FROM rgxpatterns')
        rs = d.fetchall()
        rv = {}
        if rs == None:
            return None
        else:
            for i in rs:
                rv[i[0]] = i[1]
            return rv
    
    def getLookup(self, logid):
        # returns items of lookup with logid
        if logid == 0:
            # Just return last one
            d = self.cursor.execute('SELECT id, filename, type, age, state FROM log WHERE logsid=(SELECT logsid FROM logs ORDER BY id  DESC LIMIT 1)')
        else:
            d = self.cursor.execute('SELECT * FROM log WHERE logsid="' + str(logid) + '"')
        rs = d.fetchall()
        rv = []
        if rs == None:
            return None
        else:
            for i in rs:
                rv.append({'id': i[0], 'filename': i[1], 'ftype': i[2], 'age': i[3], 'state': i[4]})
            return rv
        
    def getItems(self):
        # returns all existing items in the database
        d = self.cursor.execute('SELECT i.id, i.filename, i.state, k.lookuptime FROM log AS i INNER JOIN logs as k ON (k.id=i.logsid) AND (i.state<20)')
        rs = d.fetchall()
        rv = []
        if rs == None:
            return None
        else:
            for i in rs:
                rv.append({'id': i[0], 'filename': i[1], 'state': i[2], 'lookuptime': i[3]})
            return rv
        
# Command Line Interface for Settings:
class cli:
    def __init__(self, dbpath):
        cmds = {
            'list':  {'txt': 'List', 'subc': {
                'ftypes': {'txt': 'List Filetypes', 'a': self.listTypes}, 
                'fnames': {'txt': 'List Filename patterns', 'a': self.listFnpatterns}, 
                }
            }, 
            'scan': {'txt': 'Scan folder', 'param': 1, 'a':self.scanpath}, 
        }
        if len(sys.argv) < 2:
            self.pshowavailable(cmds)
            sys.exit()
        self.parseargs(sys.argv[1:len(sys.argv)], cmds)
    
    
    # parse arguments
    def parseargs(self, arglist, cmdlist):
        # if command exist in given cmdlist
        if arglist[0] in cmdlist.keys():
            # if command has subcommands
            if 'subc' in cmdlist[arglist[0]].keys():
                # if arguments are not given
                if len(arglist) < 2:
                    print "Missing operand for: %s" % cmdlist[arglist[0]]['txt']
                    self.pshowavailable(cmdlist[arglist[0]]['subc'])
                    sys.exit()
                # parse sub commands
                self.parseargs(arglist[1:len(arglist)], cmdlist[arglist[0]]['subc'])
            else:
                # if a parameter is required
                if 'param' in cmdlist[arglist[0]].keys():
                    # if parameter is missing
                    if len(arglist) < cmdlist[arglist[0]]['param'] + 1:
                        print "Mmissing Parameter"
                        sys.exit()
                    # action with params
                    cmdlist[arglist[0]]['a'](arglist[1])
                else:
                    # action
                    cmdlist[arglist[0]]['a']()
        else:
            print 'Unknown command: %s' % arglist[0]
            self.pshowavailable(cmdlist)
    
    # show available commands
    def pshowavailable(self, c):
        print "Available commands:"
        for i in c.keys():
            print "\t%s:\t%s" % (i, c[i]['txt'])
    
    # list file types
    def listTypes(self):
        print "Listing file types"
    
    # list filename patterns
    def listFnpatterns(self):
        print "Listing filename patterns"
    
    # scan
    def scanpath(self, spath):
        print "Scan folder: %s" % spath
        import lookup
        lp = lookup.lookPath(spath)
        lp.start()
        import time
        print '\n'
        while lp.isAlive():
            sys.stdout.write('\r')
            sys.stdout.flush()
            ttp = "Checking %d items. Current: %s" % (lp.founditems, lp.currentitem)
            sys.stdout.write(ttp)
            sys.stdout.flush()
            time.sleep(.3)
        #match results
        import matchfile
        pc = matchfile.phrasechecker()
        for i in lp.items:
            # identify
            print i
        # record log: filename, lastModTime, tag, proposedRelocationTime
        
if __name__ == "__main__":
    d = dbi(defaultDbPath)
