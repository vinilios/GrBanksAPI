#!/usr/bin/python

import unicode_excel_write
import urllib, urllib2, cookielib
from lxml import html
import unicode_excel_write
import code, time

class BaseBank(object):
    def __init__(self,name):
        self.opener = urllib2.build_opener(
            urllib2.HTTPRedirectHandler(),
            urllib2.HTTPHandler(debuglevel=0), #debug
            urllib2.HTTPSHandler(debuglevel=0), #debug
            urllib2.HTTPCookieProcessor(cookielib.CookieJar()) #cookielib.MozillaCookieJar(cookie_filename)
        )
        self.opener.addheaders = [('User-agent', 'Mozilla/5.0')]
        self.name = name
        
    def openUrl(self, url, params=None):
        if params==None:
            g = self.opener.open(url)
        else:
            g = self.opener.open(url, urllib.urlencode(params))
        s = g.read()
        v = html.document_fromstring(s)
        g.close()
        return (s,v)
        
    def manage_up(self,user,passw,acnt):
        if passw==None:
            # in this case the first argument is a configuration file
            passw=user.get(self.name,'pass')
            acnt=user.get(self.name,'acnt')
            user=user.get(self.name,'user')
        return (user, passw, acnt)
        
    def toCsv(self, filename):
        fo = open(filename, 'wb')
        g = unicode_excel_write.UnicodeWriter(fo)
        g.writerows([(time.strftime('%d/%m/%Y',a),b,c,d) for (a,b,c,d) in self.table])
        g.writerow(["total: ","",self.left])
        fo.close()

    def printp(self):
        print "\n".join([("%s %s %s %s" % (time.strftime('%d/%m/%Y',a),b,c.encode('utf-8'),d)) for (a,b,c,d) in self.table])
        print "-------------------------------------------------"
        print "                                  total: %4s" % self.left

    def __add__(self, other):
        b = BaseBank("%s_%s"%(self.name,other.name))
        b.left = "%3.2f" % (float(self.left)+float(other.left))
        b.table = sorted(self.table+other.table)
        return b