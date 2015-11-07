#!/usr/bin/python

# This is a Python script to download HD trailers from the Apple Trailers
# website. It uses the "Just Added" JSON endpoint to discover new trailers and
# keeps track of the ones it has already downloaded so they aren't
# re-downloaded.
#
# Started on: 10.14.2011
#
# Copyright 2011-2014 Adam Goforth
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

# Some imports are declared inside of functions, so other functions in this
# script can be used in other scripts, without requiring all of
# the dependencies.
import codecs
import re
import urllib
import urllib2
import os.path
import shutil
from bs4 import BeautifulSoup

#############
# Functions #
#############
def getTrailerFileUrls(pageUrl, res, types):
    iTunesResolutions = ['720', '1080']
    webResolutions = ['480', '720']

    urls = []

    # Order matters here. Prefer the iTunes files over the web files.
    if res in iTunesResolutions:
        urls = getITunesTrailersFileUrls(pageUrl, res, types)
    elif res in webResolutions:
        urls = getWebTrailersFileUrls(pageUrl, res, types)
    else:
        uniqueResolutions = list(set(iTunesResolutions + webResolutions))
        resString = ', '.join(uniqueResolutions)
        raise ValueError("Invalid resolution. Valid values: %s" % resString)

    return urls

def getITunesTrailersFileUrls(pageUrl, res, types):
    """Take a trailer page URL and convert it to the URL of the trailer .mov file in the desired resolution"""
    """The trailer file URL is pulled out of the 'iTunes' .inc file on the server."""

    incUrl = pageUrl + '/includes/playlists/itunes.inc'
    incPage = urllib.urlopen(incUrl)
    incContents = incPage.read()
    incSoup = BeautifulSoup(incContents, 'html.parser')

    linkMatcher = "_h%sp\.mov" % res
    links = incSoup.findAll(href=re.compile(linkMatcher))
    
    if (len(links) == 0):
        # Go down in resolution if file not found
        if res == '1080':
            print "Could not find a trailer file URL with resolution '%s'. Retrying with '720'" % res
            return getITunesTrailersFileUrls(pageUrl, '720')
        if res == '720':
            print "Could not find a trailer file URL with resolution '%s'. Retrying with the 'web' source" % res
            return getWebTrailersFileUrls(pageUrl, '720')
        print 'Error finding the trailer file URL'
        return []

    urls = []
    for link in links:
        videoType = link.find_parent(class_='trailer').find('h3').string
        url = link['href']

        if shouldDownloadFile(types, videoType, url):
            urlInfo = {
                    'url': url,
                    'type': videoType,
                    'res': res
            }
            urls.append(urlInfo)

    return urls

def getWebTrailersFileUrls(pageUrl, res, types):
    """Take a trailer page URL and convert it to the URL of the trailer .mov file in the desired resolution"""
    """The trailer file URL is pulled out of the 'web' HTML file on the server."""
    resSegment = 'extralarge'
    if (res == '480'):
        resSegment = 'large'

    # Get the page that describes which videos are available
    incUrl = pageUrl + 'includes/' + resSegment + '.html'
    incPage = urllib.urlopen(incUrl)
    incContents = incPage.read()
    incSoup = BeautifulSoup(incContents, 'html.parser')
    trailerElements = incSoup.findAll('li', class_='trailer')

    if (len(trailerElements) == 0):
        # Some trailers might only have a 480p file
        if res == '720':
            print "Could not find a trailer file URL with resolution '%s'. Retrying with '480'" % res
            return getWebTrailersFileUrls(pageUrl, '480')
        print 'Error finding the trailer file URL'
        return []

    urls = []
    for element in trailerElements:
        videoType = element.find('h3').string

        if shouldDownloadFile(types, videoType, ''):
            # The video file URL is only in a separate include file
            includeFileUrl = pageUrl + element.find('a', class_='link-play')['href']
            incPage = urllib.urlopen(includeFileUrl)
            incContents = incPage.read()
            incSoup = BeautifulSoup(incContents, 'html.parser')
             
            url = incSoup.find('a', class_='movieLink')['href']

            # Change link URL to the download URL by changing e.g. _720p to _h720p
            url = re.sub('_(\d+)p', '_h\\1p', url)

            urlInfo = {
                    'url': url,
                    'type': videoType,
                    'res': res
            }
            urls.append(urlInfo)

    return urls

def shouldDownloadFile(requestedTypes, videoType, url):
    doDownload = False

    if requestedTypes == 'all':
        doDownload = True

    elif requestedTypes == 'single_trailer':
        doDownload = (videoType.lower() == 'trailer')
    
    elif requestedTypes == 'trailers':
        if (videoType.lower().startswith('trailer') or
            videoType.lower().startswith('teaser') or
            videoType.lower() == 'first look'):
            doDownload = True

    return doDownload

def getTrailerTitle(pageUrl):
    """Take a trailer page URL and return the title of the film, taken from the title tag on the page"""
    trPage = urllib.urlopen(pageUrl)
    trContents = trPage.read()
    trSoup = BeautifulSoup(trContents, 'html.parser')
    titleTag = trSoup.html.head.title.string

    titleParts = titleTag.split(' - ')
    return titleParts[0]

def getDownloadedFiles(dlListPath):
    """Get the list of downloaded files from the text file"""
    fileList = []
    if (os.path.exists(dlListPath)):
        f = codecs.open(dlListPath, 'r', encoding='utf-8')
        for line in f.xreadlines():
            fileList.append(convertToUnicode(line.strip()))
        f.close()
    return fileList

def writeDownloadedFiles(fileList, dlListPath):
    """Write the list of downloaded files to the text file"""
    f = open(dlListPath, 'w')
    newList = [(filename + '\n').encode('utf-8') for filename in fileList]
    f.writelines(newList)
    f.close()

def recordDownloadedFile(filename, dlListPath):
    """Appends the given filename to the text file of already downloaded files"""
    fileList = getDownloadedFiles(dlListPath)
    fileList.append(filename)
    writeDownloadedFiles(fileList, dlListPath)

def downloadTrailerFile(url, destdir, filename):
    """Accepts a URL to a trailer video file and downloads it"""
    """You have to spoof the user agent or the site will deny the request"""
    filePath = os.path.join(destdir, filename)

    existingFileSize = 0
    if os.path.exists(filePath):
        existingFileSize = os.path.getsize(filePath)

    data = None
    headers = { 'User-Agent' : 'QuickTime/7.6.2' }
    req = urllib2.Request(url, data, headers)
    f = urllib2.urlopen(req)
    metaInfo = f.info()
    dlFileSize = int(metaInfo.getheaders("Content-Length")[0])

    if dlFileSize == existingFileSize:
        print "*** File already downloaded, skipping."
    else:
        print "Saving file to %s" % filePath
        # Buffer 1MB at a time
        chunkSize = 1024 * 1024
        with open(filePath, 'wb') as fp:
            shutil.copyfileobj(f, fp, chunkSize)

def downloadTrailersFromPage(pageUrl, title, dlListPath, res, destdir, types):
    """Takes a page on the Apple Trailers website and downloads the trailer for the movie on the page"""
    """Example URL: http://trailers.apple.com/trailers/lions_gate/thehungergames/"""
    print 'Checking for ' + title
    trailerUrls = getTrailerFileUrls(pageUrl, res, types)
    for trailerUrl in trailerUrls:
        trailerFileName = title + '.' + trailerUrl['type'] + '.' + trailerUrl['res'] + 'p.mov'
        trailerFileName = getValidFilename(trailerFileName)
        trailerFileName = convertToUnicode(trailerFileName)
        downloadedFiles = getDownloadedFiles(dlListPath)
        if not trailerFileName in downloadedFiles:
            print 'downloading ' + trailerUrl['url']
            downloadTrailerFile(trailerUrl['url'], destdir, trailerFileName)
            recordDownloadedFile(trailerFileName, dlListPath)
        else:
            print '*** File already downloaded, skipping: ' + trailerFileName

def getValidFilename(name):
    """Remove characters from the given string which appear in a blacklist.

    The blacklist contains characters that should not be used in filenames on
    various operating systems."""
    return "".join(s for s in name if s not in "\/:*?<>|#%&{}$!'\"@+`=");

def getConfigValues(configPath, defaults):
    """Get the script's configuration values and return them in a dict
    
    If a config file exists, merge its values with the defaults. If no config
    file exists, just return the defaults.
    """
    from ConfigParser import SafeConfigParser

    config = SafeConfigParser(defaults)
    configValues = config.defaults()

    configPaths = [
        configPath,
        os.path.join(os.path.expanduser('~'), '.trailers.cfg'),
    ]

    configFileFound = False
    for path in configPaths:
        if os.path.exists(path):
            print "Loading configuration from %s" % path
            configFileFound = True
            config.read(path)
            configValues = config.defaults()
            break

    if not configFileFound:
        print 'Config file not found.  Using default values.'

    return configValues

def getSettings():
    import argparse

    # Don't include list_file in the defaults, so we can tell
    # if it was in the config file or not.
    scriptDir = os.path.abspath(os.path.dirname(__file__))
    defaults = {
        'download_dir': scriptDir,
        'resolution': '720',
        'video_types': 'single_trailer'
    }

    validResolutions = ['480', '720', '1080']
    validVideoTypes = ['single_trailer', 'trailers', 'all']

    parser = argparse.ArgumentParser(description=
            'Download movie trailers from the Apple website. With no ' +
            'arguments, will download all of the trailers in the current RSS ' +
            'feed. When a trailer page URL is specified, will only download ' +
            'the single trailer at that URL. Example URL: ' +
            'http://trailers.apple.com/trailers/lions_gate/thehungergames/')

    parser.add_argument(
        '-c, --config',
        action='store',
        dest='config',
        help='The location of the config file. Defaults to "settings.cfg"' +
                'in the script directory.'
    )

    parser.add_argument(
        '-d, --dir',
        action='store',
        dest='dir',
        help='The directory where the trailers should be downloaded. ' +
                'Defaults to the script directory.'
    )

    parser.add_argument(
        '-l, --listfile',
        action='store',
        dest='filepath',
        help='The location of the download list file. The names of the ' +
                'previously downloaded trailers are stored in this file. ' +
                'Defaults to "download_list.txt" in the download directory.'
    )

    parser.add_argument(
        '-r, --resolution',
        action='store',
        dest='resolution',
        help='The preferred video resolution to download. Valid options are ' +
                '1080, 720, and 480.'
    )

    parser.add_argument(
        '-u, --url',
        action='store',
        dest='url',
        help='The URL of the Apple Trailers web page for a single trailer.'
    )

    parser.add_argument(
        '-v, --videotypes',
        action='store',
        dest='types',
        help='The types of videos to be downloaded. Valid options are ' +
                'single_trailer, trailers, and all.'
    )

    results = parser.parse_args()
    args = {
        'config_path': results.config,
        'download_dir': results.dir,
        'list_file': results.filepath,
        'page': results.url,
        'resolution': results.resolution,
        'video_types': results.types,
    }

    # Remove all pairs that were not set on the command line.
    setArgs = {}
    for name, value in args.iteritems():
        if value is not None:
            setArgs[name] = value

    configPath = args['config_path']
    if configPath is None:
        configPath = "%s/settings.cfg" % scriptDir

    try:
        config = getConfigValues(configPath, defaults)
    except ValueError as e:
        print "Configuration error: %s" % e
        print 'Exiting...'
        exit()

    settings = config.copy()
    settings.update(setArgs)

    settings['download_dir'] = os.path.expanduser(settings['download_dir'])

    if ('list_file' not in setArgs) and ('list_file' not in config):
        settings['list_file'] = os.path.join(
            settings['download_dir'],
            'download_list.txt'
        )

    settings['list_file'] = os.path.expanduser(settings['list_file'])

    # Validate the settings
    settingsError = False
    if settings['resolution'] not in validResolutions:
        resString = ', '.join(validResolutions)
        print "Configuration error: Invalid resolution. Valid values: %s" % resString
        settingsError = True

    if not os.path.exists(settings['download_dir']):
        print 'Configuration error: The download directory must be a valid path'
        settingsError = True

    if settings['video_types'] not in validVideoTypes:
        typesString = ', '.join(validVideoTypes)
        print "Configuration error: Invalid video type. Valid values: %s" % typesString
        settingsError = True

    if not os.path.exists(os.path.dirname(settings['list_file'])):
        print 'Configuration error: the list file directory must be a valid path'
        settingsError = True

    if settingsError:
        print 'Exiting...'
        exit()

    return settings

def convertToUnicode(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj


#############
# Main Prog #
#############
if __name__ == '__main__':
    import json

    settings = getSettings()

    print "Using configuration values:"
    for name in sorted(settings):
        if name != 'config_path':
            print "    {}: {}".format(name, settings[name])

    print ""
    
    # Do the download
    if 'page' in settings:
        # The trailer page URL was passed in on the command line
        trailerTitle = getTrailerTitle(settings['page'])
        downloadTrailersFromPage(
            settings['page'],
            trailerTitle,
            settings['list_file'],
            settings['resolution'],
            settings['download_dir'],
            settings['video_types']
        )

    else:
        # Use the "Just Added" JSON file
        newestTrailers = json.load(urllib.urlopen('http://trailers.apple.com/trailers/home/feeds/just_added.json'))
    
        for trailer in newestTrailers:
            url = 'http://trailers.apple.com' + trailer['location']
            downloadTrailersFromPage(
                url,
                trailer['title'],
                settings['list_file'],
                settings['resolution'],
                settings['download_dir'],
                settings['video_types']
            )
