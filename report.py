#!/usr/bin/python
# -*- coding: utf-8 -*-

# walks in the download folder, generates a report

# Settings file:
defset = 'settings.ini'

import datetime         # age calculations
import ConfigParser     # settings.ini
import sys              # stdout
import time             # sleep

import data


if __name__ == "__main__":
    # check config:
    config = ConfigParser.ConfigParser()
    config.read(defset)
    if not "paths" in config.sections():
        config.add_section("paths")
    if not "newcomers" in config.options("paths"):
        config.set('paths','newcomers','/home/koray/.gvfs/land on 10.1.1.10/newcomers')
    if not "database" in config.options("paths"):
        config.set('paths','database','newcomers.db')
    
    cf = open(defset,'w')
    config.write(cf)
    cf.close()
    
    # read config:
    config.read(defset)
    scanpath = config.get('paths','newcomers')
    dbpath = config.get('paths','database')
    
    # check if it's been more than one hour since last lookup:
    d = data.dbi(dbpath)

    if (datetime.datetime.now() - d.getLogage()) > datetime.timedelta(hours=1):
        # get files
        import lookup
        lp = lookup.lookPath(scanpath)
        lp.start()
        print "Scanning: %s" % scanpath
        while lp.isAlive():
            sys.stdout.write('\r')
            sys.stdout.flush()
            ttp = "Checking %d items.  (%s)                             " % (lp.founditems, lp.currentitem)
            sys.stdout.write(ttp)
            sys.stdout.flush()
            time.sleep(.3)
        print "\nDone: total %d items" % lp.founditems
        print "Entering results to database"
        progress = len(lp.items)
        for i in lp.items:
            sys.stdout.write('\r')
            sys.stdout.flush()
            sys.stdout.write('%d       ' % progress)
            if i['file'] == True:
                d.addfile(i['name'], i['info'], i['modification'])
            else:
                d.addfile(i['name'], ['directory'], i['modification'])
            sys.stdout.flush()
            progress = progress - 1
        print "Done."
    
    # load results
    print "Populating data."
    r = d.getLookup(0)
    import matchfile
    c = matchfile.phrasechecker(d)
    rv = []
    for i in r:
        # file type:
        cur = {'file': i['filename']}
        curftype = c.checktype(i['ftype'])
        ltp = "%s: " % i['filename']
        if curftype == None:
            cur['filetype'] = 0     # Unknown
            ltp = ltp + ' Type: Unknown, '
        else:
            cur['filetype'] = curftype
            ltp = ltp + ' Type: %s, ' % cur['filetype']
        # filename regex matches
        cur['namergx'] = c.checkname(cur['file'])
        if 1 in cur['namergx'] and len(cur['namergx']) > 1:
            # multiple match (tv show) Check if in any defined category:
            cur['category'] = c.getCat(curftype, cur['namergx'])
            ltp = ltp + 'Category: %s, ' % cur['category']
            cur['show'] = c.parseShow(cur['file'])
            ltp = ltp + 'ShowData: %s, ' % cur['show']
            
        print ltp
        
        rv.append(cur)
    
