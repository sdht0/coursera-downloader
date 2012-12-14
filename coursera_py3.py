import os.path
import os
import sys
import urllib.request
import urllib.parse
import urllib.error
import http.cookiejar
import re
import time

try:
    from bs4 import BeautifulSoup
except ImportError as err:
    print("error: %s. Please install Beautiful Soup 4." % err)
    sys.exit(1)


class CourseraDownloader:

    def __init__(self, course, auth):
        course['login_url'] = ('https://class.coursera.org/%s/auth/auth_redirector?type=login&subtype=normal') % course['name']
        course['lectures_url'] = 'https://class.coursera.org/%s/lecture/index' % course['name']
        self.course = course
        self.auth = auth
        self.loggedin = 0

        self.cookiefilepath = course['cookiepath'] + "_" + course['name']
        self.cookie = http.cookiejar.LWPCookieJar()
        if os.path.isfile(self.cookiefilepath):
            self.cookie.load(self.cookiefilepath)
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.cookie))
        urllib.request.install_opener(opener)

        self.headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.19 (KHTML, like Gecko) Ubuntu/12.04 Chromium/18.0.1025.168 Chrome/18.0.1025.168 Safari/535.19'}

    def printerror(self, url, e):
        print('Failed to open "%s". ' % url)
        if hasattr(e, 'code'):
            print('Error code - %s. ' % e.code, end=' ')
        elif hasattr(e, 'reason'):
            print("Reason:", e.reason)

    def login(self):
        try:
            self.cookie.clear()
            url = self.course['login_url']
            req = urllib.request.Request(url, None, self.headers)
            handle = urllib.request.urlopen(req)
        except IOError as e:
            self.printerror(url, e)
            return -1
        else:
            try:
                print("Submitting form...", end=' ')
                headers = self.headers
                headers['Referer'] = handle.geturl()
                self.auth['login'] = "Login"
                url = handle.geturl()
                req = urllib.request.Request(url, urllib.parse.urlencode(self.auth).encode('utf-8'), self.headers)
                handle = urllib.request.urlopen(req)
            except IOError as e:
                self.printerror(url, e)
                return -1
            else:
                self.cookie.save(self.cookiefilepath)
                return handle

    def downloadlist(self):
        try:
            url = self.course['lectures_url']
            req = urllib.request.Request(url, None, self.headers)
            handle = urllib.request.urlopen(req)
        except IOError as e:
            self.printerror(url, e)
            return -1
        else:
            return handle

    def getdownloadlist(self):
        handle = self.downloadlist()
        if handle == -1:
            return -1
        if handle.geturl() != self.course['lectures_url']:
            print("Logging in...", end=' ')
            self.login()
            handle = self.downloadlist()
            if handle == -1:
                return -1
            if handle.geturl() != self.course['lectures_url']:
                return -1
            print("Login successful!")
        self.handle = handle
        self.html = BeautifulSoup(handle.read())
        return 0

    def downloadfile(self, url, filename):
        try:
            req = urllib.request.Request(url, None, self.headers)
            response = urllib.request.urlopen(req)
        except IOError as e:
            self.printerror(url, e)
            if(e.code != 500):
                return -1
            else:
                return 0
        x = open("temp_" + filename, "wb")
        hd = response.headers['Content-Length']
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
                    self.printerror(url, e)
                    return -1
                x.write(chunk)
                bytes_so_far += len(chunk)
                speed = bytes_so_far / (1024 * (time.time() - start_time))
                percent = round((bytes_so_far * 100.0) / total_size, 2)
                if total_size < 1024.0 * 1024.0:
                    sys.stdout.write(" Downloaded %.2f / %.2f KiB (%0.2f%% at %3d kbps)\r" %
                   (bytes_so_far / (1024.0), total_size / (1024.0), percent, speed))
                else:
                    sys.stdout.write(" Downloaded %.2f / %.2f MiB (%0.2f%% at %3d kbps)\r" %
                   (bytes_so_far / (1024.0 * 1024.0), total_size / (1024.0 * 1024.0), percent, speed))
                sys.stdout.flush()
            sys.stdout.write('\n')
        else:
            try:
                chunk = response.read()
            except IOError, e:
                self.printerror(url, e)
                return -1
            x.write(chunk)
            sys.stdout.write(" Downloaded 100%\n")
        x.close()
        os.rename("temp_" + filename, filename)
        return 0

    def downloadcontents(self):
        print("Getting downloads list...")
        ret = self.getdownloadlist()
        if ret == -1:
            return -1
        print("Downloads list obtained!")
        pcd = os.getcwd()
        os.chdir(self.course['downloadfolder'])
        if not os.path.exists(self.course['folder']):
            os.mkdir(self.course['folder'])
        os.chdir(self.course['folder'])
        count = 1
        mydiv = self.html.find("div", "item_list")
        xa = mydiv.find_all("a", "list_header_link")
        xb = mydiv.find_all("ul", "item_section_list")
        for num, i in enumerate(xa):
            title = i.find("h3").string.strip(" \r\n").lower()
            print("######### " + str(num + 1) + "." + title + " #########")
            title = re.sub(r'\([^)]*\)', '', title).strip(" \r\n")
            folder = str(num + 1) + "-" + re.sub(r'--*', '-', re.sub(r'[^A-Za-z0-9.]', '-', title))
            cd = os.getcwd()
            if not os.path.exists(folder):
                os.mkdir(folder)
            os.chdir(folder)
            items = xb[num]
            allli = items.find_all("a", "lecture-link")
            for j, x in enumerate(allli):
                ltitle = x.next_element
                ltitle = re.sub(r'\([^)]*\)', '', ltitle).strip(" \r\n").lower()
                print("*** " + str(j + 1) + ". " + ltitle + " ***")
                ele = x.parent.find("div", "item_resource")
                alla = ele.find_all("a")
                for a in alla:
                    url = a["href"]
                    ext = ""
                    if "pptx" in a["href"]:
                        ext = "pptx"
                    elif "pdf" in a["href"]:
                        ext = "pdf"
                    elif "txt" in a["href"]:
                        ext = "txt"
                    elif "srt" in a["href"]:
                        ext = "srt"
                    elif "download.mp4" in a["href"]:
                        ext = "mp4"
                    else:
                        continue
                    filename = str(num + 1) + "." + str(j + 1) + "-" + re.sub(r'--*', '-', re.sub(r'[^A-Za-z0-9.]', '-', ltitle.lower())) + "." + ext
                    if (ext in self.course['downloadlist']):
                        print("File: " + filename)
                        if(os.path.exists(filename)):
                            print("Skipping: Already exists")
                        else:
                            ret = self.downloadfile(url, filename)
                            if ret == -1:
                                return -1
                    count += 1
                print()
            os.chdir(cd)
        return 0


def main():
    args = sys.argv
    if len(args) < 2:
        print("course name missing in arguments")
        return
    try:
        from config import email, password, downloadlist, foldermapping, downloadpath
        if(email == '' or password == '' or downloadlist == []):
            print("Please edit config.py with your email, password and download file types ")
            return
        if downloadpath == '':
            downloadpath = os.getcwd()
    except ImportError as err:
        print("Error: %s. You should provide config.py with email, password, downloadlist and foldermapping" % err.message)
        return
    auth = {"email": email, "password": password}
    course = {}
    course['cookiepath'] = os.path.join(os.getcwd(), "cookies", "cookie")
    course['downloadlist'] = downloadlist
    course['downloadfolder'] = downloadpath
    for i in range(1, len(args)):
        course['name'] = args[i]
        if course['name'] in foldermapping:
            course['folder'] = foldermapping[course['name']]
        else:
            course['folder'] = course['name']
        print("\nDownloading", course['name'], "to", os.path.join(course['downloadfolder'], course['folder']), "for", auth['email'])
        c = CourseraDownloader(course, auth)
        if c.downloadcontents() == -1:
            print ("Failed :( ! Please try again")
            return
        else:
            print ("Completed downloading " + course['name'] + " to " + os.path.join(course['downloadfolder'], course['folder']))


if __name__ == "__main__":
    main()
