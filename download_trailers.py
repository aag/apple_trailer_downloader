#!/usr/bin/python

# This is a Python script to download HD trailers from the Apple Trailers website
# It uses the RSS feed to discover new trailers and keeps track of the ones
# it has already downloaded so they aren't re-downloaded.
#
# Written by: Adam Goforth
# Started on: 10.14.2011

import re
import urllib
import urllib2
import os.path
import feedparser
from BeautifulSoup import BeautifulSoup

#################
# Config values #
#################

# The resolution of the trailer to download.  Valid values are 480, 720, and 1080.
# Higher values are better quality, but much larger files
res = '1080'

# The directory that the files should be downloaded to.  Must contain a trailing slash.
destdir = os.path.dirname(__file__) + '/'

#############
# Variables #
#############
dlListPath = destdir + "download_list.txt"

#############
# Functions #
#############

def getTrailerFileUrl(pageUrl):
  """Take a trailer page URL and convert it to the URL of the trailer .mov file in the desired resolution"""
  """The trailer file URL is pulled out of a web.inc file on the server."""
  incUrl = pageUrl + 'includes/playlists/web.inc'
  incPage = urllib.urlopen(incUrl)
  incContents = incPage.read()
  incSoup = BeautifulSoup(incContents)
  links = incSoup.findAll('a', 'target-quicktimeplayer')
  for link in links:
    p = re.compile('tlr1_h' + res + 'p')
    if (p.search(link['href'])):
      return link['href']
  return ""

def getDownloadedFiles():
  f = open(dlListPath, 'r')

  fileList = []
  for line in f.xreadlines():
    fileList.append(line.strip())

  f.close()
  return fileList

def writeDownloadedFiles(fileList):
  f = open(dlListPath, 'w')

  newList = [filename + "\n" for filename in fileList]
  f.writelines(newList)
  f.close()

def recordDownloadedFile(filename):
  fileList = getDownloadedFiles()
  fileList.append(filename)
  writeDownloadedFiles(fileList)


def downloadTrailerFile(url, filename):
  """Accepts a URL to a trailers file and downloads it"""
  user_agent = 'QuickTime/7.6.2'
  data = None
  headers = { 'User-Agent' : user_agent }
  req = urllib2.Request(url, data, headers)
  f = urllib2.urlopen(req)

  filePath = destdir + filename
  CHUNK = 16 * 1024
  with open(filePath, 'wb') as fp:
    while True:
      chunk = f.read(CHUNK)
      if not chunk: break
      fp.write(chunk)

  recordDownloadedFile(filename)

feed = feedparser.parse('http://trailers.apple.com/trailers/home/rss/newtrailers.rss')

for item in feed["items"]:
  print item["title"]
  trailerUrl = getTrailerFileUrl(item["link"])
  p = re.compile("(.*) - ")
  pmatch = p.search(item["title"])
  trailerFileName = pmatch.groups()[0] + ".Trailer." + res + "p.mov"
  downloadedFiles = getDownloadedFiles()
  if trailerUrl != "":
    if not trailerFileName in downloadedFiles:
      print trailerUrl
      downloadTrailerFile(trailerUrl, trailerFileName)
    else:
      print "*** File already exists, skipping: " + trailerFileName
