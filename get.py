import os
import re
import sys

if(len(sys.argv)!=2):
    print "Please provide a course name"
    exit(1)
else:
    course=sys.argv[1]
    
try:
    from bs4 import BeautifulSoup
    from mechanize import Browser
except ImportError as err:
    print ("error: %s. Please see requirements.txt.") % err.message
    exit(1)

login_url=('https://class.coursera.org/%s/auth/auth_redirector?type=login&subtype=normal') % course
lectures_url='https://class.coursera.org/%s/lecture/index' % course
loggedin=0

br=Browser()
br.set_handle_robots(False)

try:
    from config import EMAIL, PASSWORD, dwdlist
    if(EMAIL=='' or PASSWORD==''):
		print "Please edit config.py with your EMAIL and PASSWORD"
		exit(1)
except ImportError:
    print "You should provide config.py file with EMAIL and PASSWORD."
    exit(1)

def login():
    global loggedin
    print "Logging in as",EMAIL,"..."
    try:
        br.open(login_url)
    except IOError:
        print "Error logging in!"
        exit(1)
    br.form = br.forms().next()
    br['email'] = EMAIL
    br['password'] = PASSWORD
    br.submit()
    print "Login successful!"
    loggedin=1

def download(url,mdir,filename):
    if(os.path.exists(filename)):
        print "   => Skipping: Already exists"
    else:
        if(loggedin==0):
            login()
        print "   => Downloading "+filename+"..."
        br.retrieve(url,"temp_"+filename)
        os.rename("temp_"+filename,filename)
        print "   => Download completed"
    
try:
    cfile=open(course+".html","r")
    print "Getting download list"
    html=BeautifulSoup(cfile)
    cfile.close()
except IOError:
    login()
    try:
        print "Getting download list"
        cfile=br.open(lectures_url)
        html=BeautifulSoup(cfile)
        cfile.close()
    except IOError:
        print "Error getting file!"
        exit(1)
    try:
        fl=open(course+'.html',"w")
        fl.write(html.prettify().encode('ascii','ignore'))
        fl.close()
    except IOError:
        print "Error writing to file"
        
pcd=os.getcwd()
if not os.path.exists(course):
    os.mkdir(course)
os.chdir(course)
    
count=1
mydiv=html.find("div","item_list")
xa=mydiv.find_all("a","list_header_link")
xb=mydiv.find_all("ul","item_section_list")
for num,i in enumerate(xa):
    title= i.find("h3").string.strip(" \r\n").lower()
    print "######### "+str(num+1)+"."+title+" #########"
    title=re.sub(r'\([^)]*\)', '', title).strip(" \r\n")
    folder=str(num+1)+"-"+re.sub(r'--*', '-', re.sub(r'[^A-Za-z0-9.]', '-', title))
    cd=os.getcwd()
    if not os.path.exists(folder):
        os.mkdir(folder)
    os.chdir(folder)
    items=xb[num]
    allli=items.find_all("a","lecture-link")
    for j,x in enumerate(allli):
        ltitle=x.next_element
        ltitle=re.sub(r'\([^)]*\)', '', ltitle).strip(" \r\n").lower()
        print "*** "+str(j+1)+". "+ltitle+" ***"
        ele=x.parent.find("div","item_resource")
        alla=ele.find_all("a")
        for a in alla:
            url=a["href"]
            ext=""
            if "pptx" in a["href"]:
                ext="pptx"
            elif "pdf" in a["href"]:
                ext="pdf"
            elif "txt" in a["href"]:
                ext="txt"
            elif "srt" in a["href"]:
                ext="srt"
            elif "download.mp4" in a["href"]:
                ext="mp4"
            else:
                continue
            filename=str(num+1)+"."+str(j+1)+"-"+re.sub(r'--*', '-', re.sub(r'[^A-Za-z0-9.]', '-', ltitle.lower()))+"."+ext
            if (ext in dwdlist):
                print ext+": "+filename
                download(url,title,filename)
            #else:
                #print ext+": Skipping: Not in download list"
            count+=1
        print 
    os.chdir(cd)
    print
br.close()
print "Completed downloading "+course+"."
pth=os.path.join(pcd,course+'.html')
os.remove(pth)
