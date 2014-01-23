import os, os.path
import sys
import urllib.request, urllib.parse, urllib.error, http.cookiejar
import re
import time
import traceback
import random, string

try:
    from bs4 import BeautifulSoup
except ImportError as err:
    print("error: %s. Please install Beautiful Soup 4." % err)
    sys.exit(1)

def handleError(msg, e):
    exc_type, exc_value, exc_traceback = sys.exc_info()
    lines = traceback.format_exception(exc_type, exc_value, exc_traceback)
    print(msg)
    print(e)
    print("".join(line for line in lines))
    sys.exit(1)

class CourseraDownloader:

    def __init__(self, course, auth):
        course['lectures_url'] = 'https://class.coursera.org/%s/lecture' % course['name']
        self.course = course
        self.auth = auth
        self.loggedin = 0
        if not os.path.exists("cookies"):
            os.mkdir("cookies")
        self.cookiefilepath = os.path.join(os.getcwd(), "cookies", "cookie")+"_"+course['name']
        self.cookie = http.cookiejar.LWPCookieJar()
        if os.path.isfile(self.cookiefilepath):
            self.cookie.load(self.cookiefilepath)
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie))
        urllib.request.install_opener(opener)
        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:17.0) Gecko/20100101 Firefox/17.0'}

    def login(self, loginurl):
        print("Logging in...", end=' ')
        self.cookie.clear()
        url = loginurl
        try:
            req = urllib.request.Request(url, None, self.headers)
            handle = urllib.request.urlopen(req)
        except IOError as e:
            handleError("Could not open login url",e)
        headers = self.headers
        headers['Referer'] = handle.geturl()
        headers['Origin']= 'https://accounts.coursera.org'
        headers['X-CSRFToken']= ''.join(random.choice(string.letters + string.digits) for x in range(24))
        headers['X-CSRF2-Token']= ''.join(random.choice(string.letters + string.digits) for x in range(24))
        headers['X-CSRF2-Cookie']= 'csrf2_token_%s' % ''.join(random.choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for x in range(8))
        headers['Cookie']= 'csrftoken=%s; %s=%s' % (headers['X-CSRFToken'],headers['X-CSRF2-Cookie'],headers['X-CSRF2-Token'])
        headers['X-Requested-With']= 'XMLHttpRequest'
        headers['Content-Type']= 'application/x-www-form-urlencoded'

        url = "https://accounts.coursera.org/api/v1/login"
        print("Submitting form...", end=' ')
        try:
            req = urllib.request.Request(url, urllib.parse.urlencode(self.auth).encode('utf-8'), self.headers)
            handle = urllib.request.urlopen(req)
        except IOError as e:
            handleError("Could not submit login form",e)
        self.cookie.save(self.cookiefilepath)
        print("Login successful!")
        return handle

    def downloadList(self):
        url = self.course['lectures_url']
        try:
            req = urllib.request.Request(url, None, self.headers)
            handle = urllib.request.urlopen(req)
        except IOError as e:
            handleError("Could not download files list at url: %s" % url,e)
        return handle

    def getDownloadData(self):
        fl = self.downloadList()
        if fl.geturl() != self.course['lectures_url']:
            self.login(fl.geturl())
            fl = self.downloadList()
            if fl.geturl() != self.course['lectures_url']:
                raise Exception("File list could not be retrieved successfully. Got url: "+fl.geturl())
        html = BeautifulSoup(fl.read())
        topics = html.find_all("div", "course-item-list-header")
        contents = html.find_all("ul", "course-item-list-section-list")
        alldict = []
        for itr in range(0,len(contents)):
            title=topics[itr].find("h3").contents[1].strip().lower()
            headingsdict = []
            for content in contents[itr].find_all("li"):
                links = content.find_all("a")
                heading = links[0].contents[0].strip().lower()
                linksdict = dict()
                linktypes = ['txt', 'srt', 'pdf', 'pptx', 'mp4', 'java', 'sml', 'zip']
                for link in links[1:]:
                    for linktype in linktypes:
                        if linktype in link['href']:
                            linksdict[linktype]=link['href']
                            break
                headingsdict.append({"title":heading,"values":linksdict})
            alldict.append({"title":title,"values":headingsdict})
        return alldict

    def downloadFile(self, url, filename, dtype):
        try:
            req = urllib.request.Request(url, None, self.headers)
            response = urllib.request.urlopen(req)
        except IOError as e:
            handleError("File download unsuccessful", e)
        x = open("temp_" + filename, "wb")
        hd = response.headers['Content-Length']
        def getSize(size):
            if size < 1024.0 * 1024.0:
                return "%.2f %s" % (size / (1024.0), "KiB")
            else:
                return "%.2f %s" % (size / (1024.0 * 1024.0), "MiB")
        if hd != None:
            total_size = int(hd.strip())
            chunk_size = 8192
            bytes_so_far = 0
            start_time = time.time()
            percent = 0
            while percent < 100.00:
                try:
                    chunk = response.read(chunk_size)
                except IOError as e:
                    handleError("Error downloading file", e)
                if len(chunk) == 0:
                    raise Exception("No data received!")
                x.write(chunk)
                bytes_so_far += len(chunk)
                speed = bytes_so_far / (time.time() - start_time)
                percent = round((bytes_so_far * 100.0) / total_size, 2)
                sys.stdout.write(dtype + ": Downloaded %0.2f%% (%s / %s at %sps)          \r" %
                        (percent, getSize(bytes_so_far), getSize(total_size), getSize(speed)))
                sys.stdout.flush()
        else:
            sys.stdout.write(dtype + ": Downloading...%\r")
            start_time = time.time()
            try:
                chunk = response.read()
            except IOError as e:
                handleError("Error downloading file", e)
            if len(chunk) == 0:
                raise Exception("No data received!")
            x.write(chunk)
            bytes_so_far = len(chunk)
            speed = bytes_so_far / (time.time() - start_time)
            sys.stdout.flush()
            sys.stdout.write(dtype + ": Downloaded 100.00%% (%s / %s at %sps)          \r" %
                        (getSize(bytes_so_far), getSize(bytes_so_far), getSize(speed)))
        sys.stdout.write('\n')
        x.close()
        os.rename("temp_" + filename, filename)
        return 0

    def downloadContents(self):
        print("Getting downloads list...")
        data = self.getDownloadData()
        totaltitle = len(data)
        print("Downloads list obtained!")
        os.chdir(self.course['downloadfolder'])
        if not os.path.exists(self.course['folder']):
            os.mkdir(self.course['folder'])
        os.chdir(self.course['folder'])
        if self.course['name'] in ['proglang-2012-001','dataanalysis-001']:
            data=reversed(data)
        for titleindex, title in enumerate(data):
            print("######### " + str(titleindex + 1) + "/"+ str(totaltitle) + ". " + title['title'] + " #########")
            folder = str(titleindex + 1) + "-" + re.sub(r'--*', '-', re.sub(r'[^A-Za-z0-9.]', '-', re.sub(r'\([^)]*\)', '', title['title']).strip(" \r\n")))
            cd = os.getcwd()
            if not os.path.exists(folder):
                os.mkdir(folder)
            os.chdir(folder)
            totalheadings = len(title['values'])
            for headingindex, heading in enumerate(title['values']):
                ltitle = re.sub(r'\([^)]*\)', '', heading['title']).strip(" \r\n")
                print("*** " + str(headingindex + 1) + "/"+ str(totalheadings) + ". " + ltitle + " ***")
                for dtype in self.course['downloadlist']:
                    cd2 = os.getcwd()
                    srtfolder = "srt"
                    if self.course['separatesrt'] and dtype in ['srt', 'txt']:
                        if not os.path.exists(srtfolder):
                            os.mkdir(srtfolder)
                        os.chdir(srtfolder)
                    if dtype in heading['values']:
                        filename = str(titleindex + 1) + "." + str(headingindex + 1) + "-" + re.sub(r'--*', '-', re.sub(r'[^A-Za-z0-9.]', '-', ltitle)) + "." + dtype
                        if(os.path.exists(filename)):
                            print("  " + dtype + ": Already exists")
                        else:
                            try:
                                self.downloadFile(heading['values'][dtype], filename, "  " + dtype)
                            except Exception as e:
                                print("\n  " + dtype + ": ", e, " | continue? [Y/n]: ",end='')
                                o = raw_input()
                                if o=='n':
                                    return 1
                    os.chdir(cd2)
                for typ in heading['values']:
                    if typ not in self.course['downloadlist']:
                        print("  " + typ + ": Configured not to download in config.py")
                print()
            os.chdir(cd)

def main():
    args = sys.argv
    if len(args) < 2:
        raise Exception("Course name missing in arguments")
    try:
        from config import email, password, downloadlist, foldermapping, downloadpath, separatesrt
    except ImportError as er:
        raise Exception("Error: %s. You should provide config.py with email, password, downloadlist and foldermapping" % er)
    if email == '' or password == '' or downloadlist == []:
        raise Exception("Please edit config.py with your email, password and download file types")
    if downloadpath == '':
        downloadpath = os.getcwd()
    auth = {"email": email, "password": password}
    course = {}
    course['downloadlist'] = downloadlist
    course['downloadfolder'] = downloadpath
    course['separatesrt'] = separatesrt
    for i in range(1, len(args)):
        course['name'] = args[i]
        if course['name'] in foldermapping:
            course['folder'] = foldermapping[course['name']]
        else:
            course['folder'] = course['name']
        print("\nDownloading", course['name'], "to", os.path.join(course['downloadfolder'], course['folder']), "for", auth['email'])
        c = CourseraDownloader(course, auth)
        c.downloadContents()
        print ("Completed downloading " + course['name'] + " to " + os.path.join(course['downloadfolder'], course['folder']))


if __name__ == "__main__":
    main()
