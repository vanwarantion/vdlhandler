#!/usr/bin/python
# -*- coding: utf-8 -*-

# dependencies: python-pysqlite2

# TODO: Change status of the file in the database

# Settings file:
defset = 'settings.ini'
# internal imports:
import data
import lookup
import matchfile
# external imports:
import time         # For time.sleep()
import sys          # for sys.stdout()
import datetime     # age calculations
import os           # path checking/manupilations
import shutil       # moving files

class maintainer:
    
    def __init__(self):
        # initialize routine:
        import ConfigParser     # settings.ini
        # check config:
        config = ConfigParser.ConfigParser()
        config.read(defset)
        if not "paths" in config.sections():
            config.add_section("paths")
        if not "newcomers" in config.options("paths"):
            config.set('paths','newcomers','/home/koray/.gvfs/land on 10.1.1.10/newcomers')
        if not "database" in config.options("paths"):
            config.set('paths','database','newcomers.db')
        if not "defaults" in config.options("paths"):
            config.set('paths','defaults','default.xml')
        
        cf = open(defset,'w')
        config.write(cf)
        cf.close()
        
        # read config:
        config.read(defset)
        self.scanpath = config.get('paths','newcomers')
        self.dbpath = config.get('paths','database')
        
        # get objects:
        self.d = data.dbi(self.dbpath)
        self.o = lookup.lookPath(self.scanpath)
        self.m = matchfile.phrasechecker(self.d)

    def execute(self, identifieds):
        for i in identifieds:
            #~ print "File: [%s] Age: [%s] Cat [%s]" % (i['id'], i['age'], i['cat'])
            for j in self.m.cat:
                if j['id'] == i['cat']:
                    if j['exec'] == '':
                        # no exec:
                        pass
                    if j['moveto'] == '':
                        # no move
                        pass
                    else:
                        age = datetime.datetime.now() - i['age']
                        if age > datetime.timedelta(days=j['atage']):
                            print "Moving %s to %s" % (i['filename'], j['moveto'])
                            self.checkTargetpath(j['moveto'])
                            src = os.path.join(self.scanpath, i['filename'])
                            trg = os.path.join(j['moveto'], i['filename'])
                            shutil.move(src, trg)
                            # change file status to 30:moved
                            self.d.updateFilestat(i['id'], 30)
                        else:
                            #print "File: %s is %s days old. %s required to move" % (i['filename'], age.days, j['atage'])
                            pass 

    def checkTargetpath(self, tp):
        if os.path.exists(tp) == False:
            print "path not exist:", tp
            os.makedirs(tp)

    def identify(self):
        # processes the results of last scan:
        self.ident = []
        for i in self.d.getLookup(0):
            #print i
            # identify file type:
            i['mtype'] = self.m.checktype(i['ftype'])
            if i['mtype'] is None:
                # Unknown filetype: move to a general location
                #print "Unknown filetype: %s for %s" % (i['ftype'][0:20], i['filename'])
                pass
            else:
                # identify file name:
                if i['state'] > 19:
                    continue
                i['mname'] = []
                i['mname'] = self.m.checkname(i['filename'])
                i['catid'] = 0
                i['catid'] = self.m.filecat(i['mtype'], i['mname'])
                #print "Filename Match for %s %s: %s" % (i['mtype'], i['filename'], i['mname'])
                self.ident.append({'filename': i['filename'], 
                    'id': i['id'], 
                    'type': i['mtype'], 
                    'rgx': i['mname'], 
                    'cat': i['catid'], 
                    'age': i['age']})
        return self.ident
    
    def scan(self, output = 0):
        # scans folder, updates database
        self.o.start()
        lastcount = 0
        while self.o.isAlive():
            if output == 0:
                pass
            if output == 1:
                sys.stdout.flush()
                ttp = "Checking %d items. (%s...)" % (self.o.founditems, self.o.currentitem[0:20])
                sys.stdout.write(ttp)
                sys.stdout.flush()
                sys.stdout.write('\r')
                time.sleep(.3)
            if output > 1:
                if self.o.founditems > lastcount:
                    print "Checking %s" % self.o.currentitem
                    lastcount = self.o.founditems
                    pass
        # Lookup Done:
        if output > 0:
            print "\nDone."
        lastcount = 0
        totaladded = 0
        # Adding to database:
        for i in self.o.items:
            sys.stdout.write('\r')
            sys.stdout.flush()
            sys.stdout.write('Updating database: %d / %d       ' % (lastcount, self.o.founditems))
            sys.stdout.flush()
            added = self.d.addfile(i['name'], i['info'], i['modification'])
            if added == 0:
                totaladded = totaladded + 1
            lastcount = lastcount + 1
        print "\n%d New." % (totaladded - 1)
        # Check lost files:
        allfiles = self.d.getItems()
        for i in allfiles:
            #~ print "Checking:", i['filename']
            if os.path.exists(os.path.join(self.scanpath, i['filename'])) == False:
                print "Not found: ", i['filename']
                self.d.updateFilestat(i['id'], 20)
    
        
if __name__ == "__main__":
    x = maintainer()
    x.scan(1)
    #print x.identify()
    x.execute(x.identify())
