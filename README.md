Coursera Downloader
==================
About
-----
This is a python script to download coursera lecture videos and files (updated to work with the Jan 2013 updates to coursera platform).

coursera.py has the following features:
* saves cookies
* shows download progress
* can provide multiple coursenames at once

coursera_py3.py has the same features, and works for python v3

Installation and Usage
----------------------
Requirements:
* Python 2 or 3   (http://python.org/download)
* Beautiful Soup 4    (http://www.crummy.com/software/BeautifulSoup)

First edit the config.py file and provide the following details:<br />
* username
* password
* files to download: mp4, srt, txt, pdf, pptx
* foldermapping: if you want the name of folder different from the coursename
* downloadpath: files are downloaded to current directory by default

To start downloading, execute in a terminal:<br />
    `python coursera.py coursename1 [coursename2 coursename3 ...]`<br />
Similarly for python3:<br />
    `python3 coursera_py3.py coursename1 [coursename2 coursename3 ...]`

Coursename can be determined from the url of the course.

eg: To download lectures of ml class (https://class.coursera.org/ml-2012-002/lecture/index), execute:<br />
    `python coursera.py ml-2012-002`

Multiple courses can be entered at once: <br />
    `python coursera.py ml-2012-002 crypto-2012-003 algs4partI-2012-001`

Limitations
-----------
* Initially it downloads all the lectures from the beginning.
* It does not resume incomplete downloads.

License
-------
GNU GPLv3
