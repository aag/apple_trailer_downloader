#!/usr/bin/env python

# This is a Python script to download HD trailers from the Apple Trailers
# website. It uses the same "Just Added" JSON endpoint to discover new trailers
# that is used on the trailers website and keeps track of the ones it has
# already downloaded so they aren't re-downloaded.
#
# Started on: 10.14.2011
#
# Copyright 2011-2017 Adam Goforth
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

# Some imports are declared inside of functions, so that this script can be
# used as a library from other Python scripts, without requiring unnecessary
# dependencies to be installed.
import codecs
import logging
import os.path
import shutil
import socket
import urllib
import urllib2

#############
# Functions #
#############
def getTrailerFileUrls(pageUrl, res, types):
    urls = []

    filmData = json.load(urllib.urlopen(pageUrl + '/data/page.json'))
    title = filmData['page']['movie_title']
    appleSize = mapResToAppleSize(res)
        
    for clip in filmData['clips']:
        videoType = clip['title']

        if appleSize in clip['versions']['enus']['sizes']:
            fileInfo = clip['versions']['enus']['sizes'][appleSize]
            fileUrl = convertSrcUrlToFileUrl(fileInfo['src'], res)

            if shouldDownloadFile(types, videoType):
                urlInfo = {
                        'res': res,
                        'title': title,
                        'type': videoType,
                        'url': fileUrl,
                }
                urls.append(urlInfo)
        elif shouldDownloadFile(types, videoType):
            logging.error('*** No {}p file found for {}'.format(res, videoType))

    return urls

def mapResToAppleSize(res):
    resMapping = {'480': 'sd', '720': 'hd720', '1080': 'hd1080'}
    if not res in resMapping:
        resString = ', '.join(resMapping.keys())
        raise ValueError("Invalid resolution. Valid values: %s" % resString)

    return resMapping[res]

def convertSrcUrlToFileUrl(srcUrl, res):
    srcEnding = "_%sp.mov" % res
    fileEnding = "_h%sp.mov" % res
    return srcUrl.replace(srcEnding, fileEnding)

def shouldDownloadFile(requestedTypes, videoType):
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
    """Resumes partial downloads and skips fully-downloaded files"""
    filePath = os.path.join(destdir, filename)
    fileExists = os.path.exists(filePath)

    existingFileSize = 0
    if fileExists:
        existingFileSize = os.path.getsize(filePath)

    data = None
    headers = { 'User-Agent' : 'QuickTime/7.6.2' }

    resumeDownload = False
    if fileExists and (existingFileSize > 0):
        resumeDownload = True
        headers['Range'] = 'bytes={}-'.format(existingFileSize)

    req = urllib2.Request(url, data, headers)

    try:
        f = urllib2.urlopen(req)
    except urllib2.HTTPError as e:
        if e.code == 416:
            logging.debug("*** File already downloaded, skipping")
            return
        elif e.code == 404:
            logging.error("*** Error downloading file: file not found")
            return
        else:
            logging.error("*** Error downloading file")
            return
    except urllib2.URLError as e:
        logging.error("*** Error downloading file")
        return

    # Buffer 1MB at a time
    chunkSize = 1024 * 1024

    try:
        if resumeDownload:
            logging.debug("  Resuming file %s" % filePath)
            with open(filePath, 'ab') as fp:
                shutil.copyfileobj(f, fp, chunkSize)
        else:
            logging.debug("  Saving file to %s" % filePath)
            with open(filePath, 'wb') as fp:
                shutil.copyfileobj(f, fp, chunkSize)
    except socket.error, msg:
        logging.error("*** Network error while downloading file: %s" % msg)
        return

def downloadTrailersFromPage(pageUrl, dlListPath, res, destdir, types):
    """Takes a page on the Apple Trailers website and downloads the trailer for the movie on the page"""
    """Example URL: http://trailers.apple.com/trailers/lions_gate/thehungergames/"""

    logging.debug('Checking for files at ' + pageUrl)
    trailerUrls = getTrailerFileUrls(pageUrl, res, types)
    downloadedFiles = getDownloadedFiles(dlListPath)

    for trailerUrl in trailerUrls:
        trailerFileName = getTrailerFilename(trailerUrl['title'], trailerUrl['type'], trailerUrl['res'])
        if not trailerFileName in downloadedFiles:
            logging.info('Downloading ' + trailerUrl['type'] + ': ' + trailerFileName)
            downloadTrailerFile(trailerUrl['url'], destdir, trailerFileName)
            recordDownloadedFile(trailerFileName, dlListPath)
        else:
            logging.debug('*** File already downloaded, skipping: ' + trailerFileName)

def getTrailerFilename(filmTitle, videoType, res):
    """Take video info and convert it to the correct filename.

    In addition to stripping leading and trailing whitespace from the title
    and converting to unicode, this function also removes characters that
    should not be used in filenames on various operating systems."""
    trailerFileName = filmTitle.strip() + '.' + videoType + '.' + res + 'p.mov'
    trailerFileName = convertToUnicode(trailerFileName)
    return "".join(s for s in trailerFileName if s not in "\/:*?<>|#%&{}$!'\"@+`=")

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
            configFileFound = True
            config.read(path)
            configValues = config.defaults()
            break

    if not configFileFound:
        print 'Config file not found.  Using default values.'

    return configValues

def getSettings():
    import argparse

    # Don't include list_file in the defaults, because the default value is
    # dependent on the configured download_dir, which isn't known until the
    # command line and config file have been parsed.
    scriptDir = os.path.abspath(os.path.dirname(__file__))
    defaults = {
        'download_dir': scriptDir,
        'resolution': '720',
        'video_types': 'single_trailer',
        'output_level': 'debug',
    }

    validResolutions = ['480', '720', '1080']
    validVideoTypes = ['single_trailer', 'trailers', 'all']
    validOutputLevels = ['debug', 'downloads', 'error']

    parser = argparse.ArgumentParser(description=
            'Download movie trailers from the Apple website. With no ' +
            'arguments, will download all of the trailers in the current ' +
            '"Just Added" list. When a trailer page URL is specified, will ' +
            'only download the single trailer at that URL. Example URL: ' +
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
        help='The directory to which the trailers should be downloaded. ' +
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
                '"1080", "720", and "480".'
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
                '"single_trailer", "trailers", and "all".'
    )

    parser.add_argument(
        '-o, --output_level',
        action='store',
        dest='output',
        help='The level of console output. Valid options are ' +
                '"debug", "downloads", and "error".'
    )

    results = parser.parse_args()
    args = {
        'config_path': results.config,
        'download_dir': results.dir,
        'list_file': results.filepath,
        'page': results.url,
        'resolution': results.resolution,
        'video_types': results.types,
        'output_level': results.output,
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
    settings['config_path'] = configPath

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

    if settings['output_level'] not in validOutputLevels:
        outputString = ', '.join(validOutputLevels)
        print "Configuration error: Invalid output level. Valid values: %s" % outputString
        settingsError = True

    if not os.path.exists(os.path.dirname(settings['list_file'])):
        print 'Configuration error: the list file directory must be a valid path'
        settingsError = True

    if settingsError:
        print 'Exiting...'
        exit()

    return settings

def configureLogging(output_level):
    loglevel = 'DEBUG'
    if (output_level == 'downloads'):
        loglevel = 'INFO'
    elif (output_level == 'error'):
        loglevel = 'ERROR'

    numeric_level = getattr(logging, loglevel, None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(format='%(message)s', level=loglevel)

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
    configureLogging(settings['output_level'])

    logging.debug("Using configuration values:")
    logging.debug("Loaded configuration from %s" % settings['config_path'])
    for name in sorted(settings):
        if name != 'config_path':
            logging.debug("    {}: {}".format(name, settings[name]))

    logging.debug("")
    
    # Do the download
    if 'page' in settings:
        # The trailer page URL was passed in on the command line
        downloadTrailersFromPage(
            settings['page'],
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
                settings['list_file'],
                settings['resolution'],
                settings['download_dir'],
                settings['video_types']
            )
