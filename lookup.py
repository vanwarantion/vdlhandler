#!/usr/bin/python
# -*- coding: utf-8 -*-

# TODO: Check for missing files

import os
import threading

class lookPath(threading.Thread):
    p = ''
    items = []
    founditems = 0
    currentitem = ''
    def __init__(self, path = '.'):
        threading.Thread.__init__(self)
        # initialize module
        self.p = path
        print "Location: %s" % path
    
    def run(self):
        self.items = self.__getitems(self.p)
    
    def __getitems(self, fpath, subf = False):
        # gets items in self.p location
        # checks recognized file types
        rv = []
        for i in os.listdir(self.p):
            if subf == False:
                self.currentitem = str(i)
            itemdata = {'name': str(i)}
            itemdata['info'] = self.__typecheck(i)
            if (itemdata['info'] == 'directory') and (subf == False):
                # if has subdirs and this is not one of them
                itemdata['children'] = os.listdir(os.path.join(fpath, i))
            itemdata['modification'] = os.path.getmtime(os.path.join(fpath, i))
            rv.append(itemdata)
            if subf == False:
                self.founditems = self.founditems + 1
        if subf == False:
            # print "done: total %d items" % len(rv)
            self.currentitem = ''
        return rv
    
    def __typecheck(self, fpath):
        # return file info
        fi = os.popen('file -b "' + os.path.join(self.p, fpath) + '"')
        return fi.readlines()

if __name__ == "__main__":
    lp = lookPath('/home/koray/.gvfs/land on 10.1.1.10/newcomers')
    lp.start()
    
    # lookup:
    
    import sys
    import time
    print '\n'
    while lp.isAlive():
        sys.stdout.write('\r')
        sys.stdout.flush()
        ttp = "Checking %d items.  (%s)" % (lp.founditems, lp.currentitem)
        sys.stdout.write(ttp)
        sys.stdout.flush()
        time.sleep(.3)
    print '\nDone'
    # record
    
    import data
    d = data.dbi('newcomers.db')
    for i in lp.items:
        added = d.addfile(i['name'], i['info'], i['modification'])
        if added == 0:
            print "Added: %s" % i['name']
