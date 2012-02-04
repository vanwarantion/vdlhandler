#!/usr/bin/python
# -*- coding: utf-8 -*-

# calculates type probabilities of possible tvshow video files


defaults = {'filename': [{
    'name': 'tvshow', 'patterns': [
        r"[Ss][0-9]*[Ee][0-9]*", 
        r"HDTV",  
        r"XviD"], }], 
'filetype': [{
    'name': 'video', 'patterns': [
        r"RIFF (little-endian) data"]}]}

class phrasechecker:
    import re
    def __init__(self, db):
        self.db = db
        self.tpatterns = db.getTypepatterns()
        self.npatterns = db.getNamepatterns()
        self.cat = db.getCategories()
    
    def parseShow(self, filename):
        ss = r"[Ss][0-9]*.[Ee][0-9]."
        tmpa = self.re.split(ss, filename, 1)
        if len(tmpa) < 2:
            rv = {'rlsinfo': tmpa[0]}
        else:
            se = self.__parseSE(self.re.findall(ss, filename)[0])
            rv = {'showname': tmpa[0], 'rlsinfo': tmpa[1], 'season': se['season'], 'episodes': se['episodes']}
        return rv
    
    def __parseSE(self, phrase):
        # parse season and episode number
        p = self.re.split('[s,e]+', phrase, flags=self.re.IGNORECASE)
        r = []
        for i in p:
            if i.isdigit():
                r.append(int(i))
        return {'season': r[0], 'episodes': r[1:len(r)]}
        
    
    def checkname(self, phrase):
        # checks regex and returns probability for each given type
        rv = []
        #print "Checking filename:", phrase
        # loop filename types:
        for i in self.npatterns.keys():
            #print '\t', self.npatterns[i]
            if self.re.search(self.npatterns[i], phrase):
                rv.append(i)
        return rv
        
    def checktype(self, phrase):
        # loop known filetypes
        # Burada kaldin
        for i in self.tpatterns.keys():
            if self.re.search(i, phrase):
                return self.tpatterns[i]
        return None
    
    def getCat(self, mtype, mname):
        # returns filename category:
        rv = None
        for i in self.cat:
            for f in i['filters']:
                if f[1] in mname:
                    rv = i
                else:
                    break
        return rv
    
    def filecat(self, mtype, rgx):
        #print "Looking category for [%s: %s]" % (mtype, rgx)
        maxprior = 0
        rv = 0
        for i in self.cat:
            #print i
            for j in rgx:
                if [mtype, j] in i['filters']:
                    #print "Match: %s" % i['name']
                    if i['priority'] > maxprior:
                        rv = i['id']
        return rv
    def refreshPatterns(self):
        # reloads:
        self.tpatterns = self.db.getTypepatterns()
        self.npatterns = self.db.getNamepatterns()
        self.cat = self.db.getCategories()
    
if __name__ == "__main__":
    import data
    d = data.dbi('newcomers.db')
    l = d.getLookup(0)
    
    c = phrasechecker(d)
    for i in l:
        i['mtype'] = c.checktype(i['ftype'])
        if i['mtype'] == None:
            q = raw_input('For file: "%s", Type "%s" not known. Add? (y/n): ' % (i['filename'], i['ftype']))
            if q == 'y':
                n = raw_input('Enter Tag: ')
                d.addftype(i['ftype'], n)
                c.refreshPatterns()
        else:
            # known type
            i['mname'] = c.checkname(i['filename'])
            # print i['filename'], i['mtype'], i['mname']
            
            if len(i['mname']) > 1:
                # known filename
                i['category'] = c.getCat(i['mtype'], i['mname'])
                print i
                p = c.parseShow(i['filename'])
                if 'episodes' in p.keys():
                    # Update db
                    print d.updateShow(i['category']['id'], p['season'], p['episodes'][-1], i['id'])
            else:
                print c.parseShow(i['filename'])
            
