#!/usr/bin/python

# This is a Python script to download HD trailers from the Apple Trailers
# website. It uses the "Just Added" JSON endpoint to discover new trailers and
# keeps track of the ones it has already downloaded so they aren't
# re-downloaded.
#
# Started on: 10.14.2011
#
# Copyright 2011-2013 Adam Goforth
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import re
import urllib
import urllib2
import os.path
import json
import shutil
from ConfigParser import SafeConfigParser
from BeautifulSoup import BeautifulSoup

#################################
# Load Config From settings.cfg #
#################################
scriptDir = os.path.dirname(__file__)
if (scriptDir == ""):
  scriptDir = "."
scriptDir = scriptDir + '/'
configPath = scriptDir + 'settings.cfg'

res = '720'
destdir = scriptDir
page = ''

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
  if ((res != '480') and (res != '720')):
    print "Error: Resolution must be set to 480 or 720"
    exit()

  if ((len(destdir) < 1) or (not os.path.exists(destdir))):
    print "Error: The download directory must be a valid path"
    exit()

  if (destdir[-1] != '/'):
    destdir = destdir + '/'

  parser = argparse.ArgumentParser(description=
      'Download movie trailers from the Apple website. ' +
      'With no arguments, will download all of the trailers in the current RSS feed. ' +
      'When a trailer page URL is specified, will only download the single trailer at that URL. ' + 
      '\n\nExample URL: http://trailers.apple.com/trailers/lions_gate/thehungergames/')
  parser.add_argument('-u', action="store", dest="url", help="The URL of the Apple Trailers web page for a single trailer.")
  results = parser.parse_args()
  page = results.url


#############
# Variables #
#############
dlListPath = destdir + "download_list.txt"

#############
# Functions #
#############

def getTrailerFileUrl(pageUrl):
  """Take a trailer page URL and convert it to the URL of the trailer .mov file in the desired resolution"""
  """The trailer file URL is pulled out of a JSON file on the server."""
  resSegment = "extralarge"
  if (res == '480'):
    resSegment = "large"

  incUrl = pageUrl + 'includes/trailer/' + resSegment + '.html'
  incPage = urllib.urlopen(incUrl)
  incContents = incPage.read()
  incSoup = BeautifulSoup(incContents)
  links = incSoup.findAll('a', 'movieLink')

  if (len(links) != 1):
    print "Error finding the trailer file URL"
    return ""

  url = links[0]['href']

  # Change link URL to the download URL by changing e.g. _720p to _h720p
  url = re.sub('_(\d+)p', '_h\\1p', url)

  return url

def getTrailerTitle(pageUrl):
  """Take a trailer page URL and return the title of the film, taken from the title tag on the page"""
  trPage = urllib.urlopen(pageUrl)
  trContents = trPage.read()
  trSoup = BeautifulSoup(trContents)
  titleTag = trSoup.html.head.title.string

  titleParts = titleTag.split(' - ')
  return titleParts[0]

def getDownloadedFiles():
  fileList = []

  if (os.path.exists(dlListPath)):
    f = open(dlListPath, 'r')
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
  # Buffer 1MB at a time
  chunkSize = 1024 * 1024
  with open(filePath, 'wb') as fp:
    shutil.copyfileobj(f, fp, chunkSize)

  recordDownloadedFile(filename)

def downloadTrailerFromPage(pageUrl, title):
  print "Checking for " + title
  trailerUrl = getTrailerFileUrl(pageUrl)
  trailerFileName = title + ".Trailer." + res + "p.mov"
  downloadedFiles = getDownloadedFiles()
  if trailerUrl != "":
    if not trailerFileName in downloadedFiles:
      print "downloading " + trailerUrl
      downloadTrailerFile(trailerUrl, trailerFileName)
    else:
      print "*** File already downloaded, skipping: " + trailerFileName


if page != None:
  # The trailer page URL was passed in on the command line
  trailerTitle = getTrailerTitle(page)
  downloadTrailerFromPage(page, trailerTitle)

else:
  # Use the "Just Added" JSON file
  newestTrailers = json.load(urllib.urlopen('http://trailers.apple.com/trailers/home/feeds/just_added.json'))

  for trailer in newestTrailers:
    url = "http://trailers.apple.com" + trailer["location"]
    downloadTrailerFromPage(url, trailer["title"])

