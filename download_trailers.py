#!/usr/bin/env python

"""This is a Python script to download HD trailers from the Apple Trailers
website. It uses the same "Just Added" JSON endpoint to discover new trailers
that is used on the trailers website and keeps track of the ones it has
already downloaded so they aren't re-downloaded.

Some imports are declared inside of functions, so that this script can be
# used as a library from other Python scripts, without requiring unnecessary
# dependencies to be installed.
"""

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

# Require using print as a function instead of a keyword
from __future__ import print_function

import io
import json
import logging
import os.path
import re
import shutil
import socket
import sys

try:
    # For Python 3.0 and later
    from configparser import Error
    from configparser import MissingSectionHeaderError
    from urllib.request import urlopen
    from urllib.request import Request
    from urllib.error import HTTPError
    from urllib.error import URLError
except ImportError:
    # Fall back to Python 2's naming
    from ConfigParser import Error
    from ConfigParser import MissingSectionHeaderError
    from urllib2 import urlopen
    from urllib2 import Request
    from urllib2 import HTTPError
    from urllib2 import URLError


def get_trailer_file_urls(page_url, res, types):
    """Get all trailer file URLs from the given movie page in the given
    resolution and having the given trailer types.
    """
    urls = []

    film_data = load_json_from_url(page_url + '/data/page.json')
    title = film_data['page']['movie_title']
    apple_size = map_res_to_apple_size(res)

    for clip in film_data['clips']:
        video_type = clip['title']

        if apple_size in clip['versions']['enus']['sizes']:
            file_info = clip['versions']['enus']['sizes'][apple_size]
            file_url = convert_src_url_to_file_url(file_info['src'], res)

            if should_download_file(types, video_type):
                url_info = {
                    'res': res,
                    'title': title,
                    'type': video_type,
                    'url': file_url,
                }
                urls.append(url_info)
        elif should_download_file(types, video_type):
            logging.error('*** No %sp file found for %s', res, video_type)

    return urls


def map_res_to_apple_size(res):
    """Map a video resolution to the equivalent value used in the data JSON file.
    """
    res_mapping = {'480': 'sd', '720': 'hd720', '1080': 'hd1080'}
    if res not in res_mapping:
        res_string = ', '.join(res_mapping.keys())
        raise ValueError("Invalid resolution. Valid values: %s" % res_string)

    return res_mapping[res]


def convert_src_url_to_file_url(src_url, res):
    """Convert a video source URL as specified in the data JSON to the actual
    URL used on the server."""
    src_ending = "_%sp.mov" % res
    file_ending = "_h%sp.mov" % res
    return src_url.replace(src_ending, file_ending)


def should_download_file(requested_types, video_type):
    """Given the requested video types and the specified video type of a particular file,
    return true if the video file should be downloaded.
    """
    do_download = False

    if requested_types == 'all':
        do_download = True

    elif requested_types == 'single_trailer':
        do_download = (video_type.lower() == 'trailer')

    elif requested_types == 'trailers':
        if (video_type.lower().startswith('trailer') or
                video_type.lower().startswith('teaser') or
                video_type.lower() == 'first look'):
            do_download = True

    return do_download


def get_downloaded_files(dl_list_path):
    """Get the list of downloaded files from the text file"""
    file_list = []
    if os.path.exists(dl_list_path):
        utf8_file = io.open(dl_list_path, mode='r', encoding='utf-8')
        for line in utf8_file:
            file_list.append(line.strip())
        utf8_file.close()
    return file_list


def write_downloaded_files(file_list, dl_list_path):
    """Write the list of downloaded files to the text file"""
    new_list = [convert_to_unicode(filename + '\n') for filename in file_list]
    downloads_file = io.open(dl_list_path, mode='w', encoding='utf-8')
    downloads_file.writelines(new_list)
    downloads_file.close()


def record_downloaded_file(filename, dl_list_path):
    """Appends the given filename to the text file of already downloaded files"""
    file_list = get_downloaded_files(dl_list_path)
    file_list.append(filename)
    write_downloaded_files(file_list, dl_list_path)


def download_trailer_file(url, destdir, filename):
    """Accepts a URL to a trailer video file and downloads it
    You have to spoof the user agent or the site will deny the request
    Resumes partial downloads and skips fully-downloaded files"""
    file_path = os.path.join(destdir, filename)
    file_exists = os.path.exists(file_path)

    existing_file_size = 0
    if file_exists:
        existing_file_size = os.path.getsize(file_path)

    data = None
    headers = {'User-Agent': 'Quick_time/7.6.2'}

    resume_download = False
    if file_exists and (existing_file_size > 0):
        resume_download = True
        headers['Range'] = 'bytes={}-'.format(existing_file_size)

    req = Request(url, data, headers)

    try:
        server_file_handle = urlopen(req)
    except HTTPError as ex:
        if ex.code == 416:
            logging.debug("*** File already downloaded, skipping")
            return
        elif ex.code == 404:
            logging.error("*** Error downloading file: file not found")
            return

        logging.error("*** Error downloading file")
        return
    except URLError as ex:
        logging.error("*** Error downloading file")
        return

    # Buffer 1MB at a time
    chunk_size = 1024 * 1024

    try:
        if resume_download:
            logging.debug("  Resuming file %s", file_path)
            with open(file_path, 'ab') as local_file_handle:
                shutil.copyfileobj(server_file_handle, local_file_handle, chunk_size)
        else:
            logging.debug("  Saving file to %s", file_path)
            with open(file_path, 'wb') as local_file_handle:
                shutil.copyfileobj(server_file_handle, local_file_handle, chunk_size)
    except socket.error as ex:
        logging.error("*** Network error while downloading file: %s", ex)
        return


def download_trailers_from_page(page_url, dl_list_path, res, destdir, types):
    """Takes a page on the Apple Trailers website and downloads the trailer for the movie on
    the page. Example URL: http://trailers.apple.com/trailers/lions_gate/thehungergames/"""

    logging.debug('Checking for files at ' + page_url)
    trailer_urls = get_trailer_file_urls(page_url, res, types)
    downloaded_files = get_downloaded_files(dl_list_path)

    for trailer_url in trailer_urls:
        trailer_file_name = get_trailer_filename(trailer_url['title'], trailer_url['type'],
                                                 trailer_url['res'])
        if trailer_file_name not in downloaded_files:
            logging.info('Downloading ' + trailer_url['type'] + ': ' + trailer_file_name)
            download_trailer_file(trailer_url['url'], destdir, trailer_file_name)
            record_downloaded_file(trailer_file_name, dl_list_path)
        else:
            logging.debug('*** File already downloaded, skipping: ' + trailer_file_name)


def get_trailer_filename(film_title, video_type, res):
    """Take video info and convert it to a safe, normalized filename.

    In addition to stripping leading and trailing whitespace from the title
    and converting to unicode, this function also removes characters that
    should not be used in filenames on various operating systems."""
    trailer_file_name = ''.join(s for s in film_title if s not in r'\/:*?<>|#%&{}$!\'"@+`=')
    # Remove repeating spaces
    trailer_file_name = re.sub(r'\s\s+', ' ', trailer_file_name)
    trailer_file_name = trailer_file_name.strip() + '.' + video_type + '.' + res + 'p.mov'
    return convert_to_unicode(trailer_file_name)


def get_config_values(config_path, defaults):
    """Get the script's configuration values and return them in a dict

    If a config file exists, merge its values with the defaults. If no config
    file exists, just return the defaults.
    """

    try:
        # For Python 3.0 and later
        from configparser import ConfigParser
    except ImportError:
        # Fall back to Python 2's naming
        from ConfigParser import SafeConfigParser as ConfigParser

    config = ConfigParser(defaults)
    config_values = config.defaults()

    config_paths = [
        config_path,
        os.path.join(os.path.expanduser('~'), '.trailers.cfg'),
    ]

    config_file_found = False
    for path in config_paths:
        if os.path.exists(path):
            config_file_found = True
            config.read(path)
            config_values = config.defaults()
            break

    if not config_file_found:
        print('Config file not found.  Using default values.')

    return config_values


def get_settings():
    """Validate and return the user's settings as a combination of the default settings,
    the settings file (if it exists) and the command-line options (if given).
    """

    # Don't include list_file in the defaults, because the default value is
    # dependent on the configured download_dir, which isn't known until the
    # command line and config file have been parsed.
    script_dir = os.path.abspath(os.path.dirname(__file__))
    defaults = {
        'download_dir': script_dir,
        'resolution': '720',
        'video_types': 'single_trailer',
        'output_level': 'debug',
    }

    valid_resolutions = ['480', '720', '1080']
    valid_video_types = ['single_trailer', 'trailers', 'all']
    valid_output_levels = ['debug', 'downloads', 'error']

    args = get_command_line_arguments()

    config_path = "{}/settings.cfg".format(script_dir)
    if 'config_path' in args:
        config_path = args['config_path']

    config = get_config_values(config_path, defaults)

    settings = config.copy()
    settings.update(args)

    settings['download_dir'] = os.path.expanduser(settings['download_dir'])
    settings['config_path'] = config_path

    if ('list_file' not in args) and ('list_file' not in config):
        settings['list_file'] = os.path.join(
            settings['download_dir'],
            'download_list.txt'
        )

    settings['list_file'] = os.path.expanduser(settings['list_file'])

    # Validate the settings
    settings_error = False
    if settings['resolution'] not in valid_resolutions:
        res_string = ', '.join(valid_resolutions)
        print("Configuration error: Invalid resolution. Valid values: %s" % res_string)
        settings_error = True

    if not os.path.exists(settings['download_dir']):
        print('Configuration error: The download directory must be a valid path')
        settings_error = True

    if settings['video_types'] not in valid_video_types:
        types_string = ', '.join(valid_video_types)
        print("Configuration error: Invalid video type. Valid values: %s" % types_string)
        settings_error = True

    if settings['output_level'] not in valid_output_levels:
        output_string = ', '.join(valid_output_levels)
        print("Configuration error: Invalid output level. Valid values: %s" % output_string)
        settings_error = True

    if not os.path.exists(os.path.dirname(settings['list_file'])):
        print('Configuration error: the list file directory must be a valid path')
        settings_error = True

    if settings_error:
        print('Exiting...')
        exit()

    return settings


def get_command_line_arguments():
    """Return a dictionary containing all of the command-line arguments
    specified when the script was run.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Download movie trailers from the Apple website. With no arguments, will' +
        'download all of the trailers in the current "Just Added" list. When a trailer page ' +
        'URL is specified, will only download the single trailer at that URL. Example URL: ' +
        'http://trailers.apple.com/trailers/lions_gate/thehungergames/'
    )

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
    set_args = {}
    for name in args:
        if args[name] is not None:
            set_args[name] = args[name]

    return set_args


def configure_logging(output_level):
    """Configure the logger to print messages with at least the level of the given
    configuration value.
    """
    loglevel = logging.DEBUG
    if output_level == 'downloads':
        loglevel = logging.INFO
    elif output_level == 'error':
        loglevel = logging.ERROR

    logging.basicConfig(format='%(message)s')
    logging.getLogger().setLevel(loglevel)


def convert_to_unicode(value):
    """In Python 2, convert the given string to a unicode string. In Python 3, just return the
    string, because it always has to be a unicode string.
    """
    if sys.version_info < (3,):
        if isinstance(value, basestring):
            if not isinstance(value, unicode):
                value = unicode(value, 'utf-8')
        return value

    return value


def load_json_from_url(url):
    """Takes a URL and returns a Python dict representing the JSON of the URL's contents."""
    response = urlopen(url)
    str_response = response.read().decode('utf-8')
    return json.loads(str_response)


def main():
    """The main script function.
    """
    try:
        settings = get_settings()
    except MissingSectionHeaderError:
        print('Configuration file is missing a header section, ' +
              'try adding [DEFAULT] at the top of the file')
        return
    except Error as ex:
        print("Configuration error: %s" % ex)
        return

    configure_logging(settings['output_level'])

    logging.debug("Using configuration values:")
    logging.debug("Loaded configuration from %s", settings['config_path'])
    for name in sorted(settings):
        if name != 'config_path':
            logging.debug("    %s: %s", name, settings[name])

    logging.debug("")

    # Do the download
    if 'page' in settings:
        # The trailer page URL was passed in on the command line
        download_trailers_from_page(
            settings['page'],
            settings['list_file'],
            settings['resolution'],
            settings['download_dir'],
            settings['video_types']
        )

    else:
        just_added_url = 'http://trailers.apple.com/trailers/home/feeds/just_added.json'
        newest_trailers = load_json_from_url(just_added_url)

        for trailer in newest_trailers:
            url = 'http://trailers.apple.com' + trailer['location']
            download_trailers_from_page(
                url,
                settings['list_file'],
                settings['resolution'],
                settings['download_dir'],
                settings['video_types']
            )


if __name__ == '__main__':
    main()
