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
from ConfigParser import SafeConfigParser
from BeautifulSoup import BeautifulSoup

###############
# Load Config #
###############
scriptDir = os.path.dirname(__file__) + '/'
configPath = scriptDir + 'settings.cfg'

res = '720'
destdir = scriptDir

if (not os.path.exists(configPath)):
  print "No config file found.  Using defaults values."
  print "  Resolution: " + res + "p"
  print "  Download Directory: " + destdir
else:
  config = SafeConfigParser(
    defaults = {
      'resolution': res,
      'download_dir': destdir
    }
  )
  config.read(configPath)

  configValues = config.defaults()
  res = configValues['resolution']
  destdir = configValues['download_dir']

  # Validate the config options
  if ((res != '480') and (res != '720') and (res != '1080')):
    print "Error: Resolution must be set to 480, 720, or 1080"
    exit()

  if ((len(destdir) < 1) or (not os.path.exists(destdir))):
    print "Error: The download directory must be a valid path"
    exit()

  if (destdir[-1] != '/'):
    destdir = destdir + '/'


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
