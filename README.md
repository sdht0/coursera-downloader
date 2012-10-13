Coursera Downloader
==================
license: GPLv3

This is a python script to download coursera lecture videos and files.

coursera.py has the following features:
* rewritten with a class structure
* saves cookies
* shows download progress
* can provide multiple coursenames at once

get.py is the original script I had written. It has been kept here for reference purposes.

Requirements:
* Python 2.6          (http://python.org/download)
* Beautiful Soup 4    (http://www.crummy.com/software/BeautifulSoup)

First edit the config.py file and provide the following details:<br />
* username
* password
* files to download: mp4, srt, txt, pdf, pptx
* foldermapping: if you want the name of folder different from the coursename
* downloadpath: files are downloaded to current directory by default

To start downloading, execute in a terminal:<br />
    `python coursera.py coursename1 [coursename2 coursename3 ...]`

Coursename can be determined from the url of the course.
eg: https://class.coursera.org/ml-2012-002/lecture/index
To download lectures of ml class, execute:<br />
    `python coursera.py ml-2012-002`

Multiple courses can be supplied at once: <br />
    `python coursera.py ml-2012-002 crypto-2012-003 algs4partI-2012-001`

Limitations:
* Initially it will download all the lectures from the beginning.
* It does not resume incomplete downloads.
