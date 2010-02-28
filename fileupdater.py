import urllib, urllib2, os

opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
urllib2.install_opener(opener)

def getResponse(url, postData = None):
    header = { 'User-Agent' : 'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.0',
               'Accept-Language': 'de',
               'Accept-Encoding': 'utf-8'
             }
    if(postData is not None):
        postData = urllib.urlencode(postData)
    req = urllib2.Request(url, postData, header)
    try:
        return urllib2.urlopen(req)
    except urllib2.HTTPError, e:
        print 'Error Code:', e.code
    except ValueError, e:
        print "invalid URL:" + url
    except urllib2.URLError, e:
        print 'Reason:', e.reason
    return None

class File:
    def __init__(self, url, localpath, response=None, test=True):
        self.name = os.path.basename(localpath)
        self.web = url
        self.local = localpath
        self.response = None
        self.oldlen = None
        self.newlen = None
        self.newcontent = None
        self.isnew = None
        self.haschanged = None
        self.test = test
        self.update()

    def update(self):
        if self.check():
            self.download()

    def check(self):
        return self.isNew() or self.hasChanged()

    def isNew(self):
        if self.isnew is None:
            self.isnew = not os.path.exists(self.local)
        return self.isnew

    def hasChanged(self):
        if self.haschanged is None:
            if self.isNew():
                self.haschanged = False
            else:
                newlen = self.getNewLen()
                self.haschanged = newlen is not None and (self.getOldLen() != newlen)
        return self.haschanged

    def getOldLen(self):
        if self.oldlen is None:
            self.oldlen = int(os.stat(self.local).st_size)
        return self.oldlen

    def getNewLen(self):
        if self.newlen is None:
            response = self.getResponse()
            if response is None:
                return None
            elif response.info().get("Content-Length") is None:
                self.newlen = len(self.getNewContent())
            else:
                self.newlen = int(response.info().get("Content-Length"))
        return self.newlen

    def getNewContent(self):
        if self.newcontent is None and self.getResponse() is not None:
            self.newcontent = self.response.read()
        return self.newcontent

    def getResponse(self):
        if self.response is None:
            self.response = getResponse(self.web, None)
        return self.response

    def download(self):
        newcontent = self.getNewContent()
        if newcontent is not None:
            localdir = os.path.dirname(self.local)
            if not os.path.exists(localdir):
                if not self.test:
                    os.makedirs(localdir)
                print "makedirs: " + localdir
            if not self.test:
                try:
                    file = open(self.local, "w")
                    file.write(newcontent)
                    file.close()
                except IOError, e:
                    print "IOError: " + e + ", " + self.local
            print "write: " + self.local

    def __str__(self):
        return self.name

class Filegroup:
    def __init__(self, remote, local, start=1, test=False):
        self.remote = remote
        self.local = local
        self.start = start
        self.test = test

    def download(self):
        i, errors = self.start, 0
        while 1 < errors:
            remote, local = self.getFile(i)
            try:
                response = urllib2.urlopen(remote)
                File(remote, local, response=response, test=self.test)
                i, errors = i + 1, 0
            except urllib2.HTTPError:
                i, errors = i + 1, errors + 1
        return i - 3

    def getFileById(self, i):
        return self.remote.format(i), self.local.format(i)  
