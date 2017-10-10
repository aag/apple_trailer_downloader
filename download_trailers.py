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
import json
import logging
import os.path
import shutil
import socket
import urllib
import urllib2


def get_trailer_file_urls(page_url, res, types):
    urls = []

    film_data = json.load(urllib.urlopen(page_url + '/data/page.json'))
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
            logging.error('*** No {}p file found for {}'.format(res, video_type))

    return urls


def map_res_to_apple_size(res):
    res_mapping = {'480': 'sd', '720': 'hd720', '1080': 'hd1080'}
    if not res in res_mapping:
        res_string = ', '.join(res_mapping.keys())
        raise ValueError("Invalid resolution. Valid values: %s" % res_string)

    return res_mapping[res]


def convert_src_url_to_file_url(src_url, res):
    src_ending = "_%sp.mov" % res
    file_ending = "_h%sp.mov" % res
    return src_url.replace(src_ending, file_ending)


def should_download_file(requested_types, video_type):
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
        f = codecs.open(dl_list_path, 'r', encoding='utf-8')
        for line in f.xreadlines():
            file_list.append(convert_to_unicode(line.strip()))
        f.close()
    return file_list


def write_downloaded_files(file_list, dl_list_path):
    """Write the list of downloaded files to the text file"""
    f = open(dl_list_path, 'w')
    new_list = [(filename + '\n').encode('utf-8') for filename in file_list]
    f.writelines(new_list)
    f.close()


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
    chunk_size = 1024 * 1024

    try:
        if resume_download:
            logging.debug("  Resuming file %s" % file_path)
            with open(file_path, 'ab') as fp:
                shutil.copyfileobj(f, fp, chunk_size)
        else:
            logging.debug("  Saving file to %s" % file_path)
            with open(file_path, 'wb') as fp:
                shutil.copyfileobj(f, fp, chunk_size)
    except socket.error, msg:
        logging.error("*** Network error while downloading file: %s" % msg)
        return


def download_trailers_from_page(page_url, dl_list_path, res, destdir, types):
    """Takes a page on the Apple Trailers website and downloads the trailer for the movie on the page
    Example URL: http://trailers.apple.com/trailers/lions_gate/thehungergames/"""

    logging.debug('Checking for files at ' + page_url)
    trailer_urls = get_trailer_file_urls(page_url, res, types)
    downloaded_files = get_downloaded_files(dl_list_path)

    for trailer_url in trailer_urls:
        trailer_file_name = get_trailer_filename(trailer_url['title'], trailer_url['type'], trailer_url['res'])
        if not trailer_file_name in downloaded_files:
            logging.info('Downloading ' + trailer_url['type'] + ': ' + trailer_file_name)
            download_trailer_file(trailer_url['url'], destdir, trailer_file_name)
            record_downloaded_file(trailer_file_name, dl_list_path)
        else:
            logging.debug('*** File already downloaded, skipping: ' + trailer_file_name)


def get_trailer_filename(film_title, video_type, res):
    """Take video info and convert it to the correct filename.

    In addition to stripping leading and trailing whitespace from the title
    and converting to unicode, this function also removes characters that
    should not be used in filenames on various operating systems."""
    trailer_file_name = film_title.strip() + '.' + video_type + '.' + res + 'p.mov'
    trailer_file_name = convert_to_unicode(trailer_file_name)
    return "".join(s for s in trailer_file_name if s not in r'\/:*?<>|#%&{}$!\'"@+`=')


def get_config_values(config_path, defaults):
    """Get the script's configuration values and return them in a dict

    If a config file exists, merge its values with the defaults. If no config
    file exists, just return the defaults.
    """
    from ConfigParser import SafeConfigParser

    config = SafeConfigParser(defaults)
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
        print 'Config file not found.  Using default values.'

    return config_values


def get_settings():
    import argparse

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
    set_args = {}
    for name, value in args.iteritems():
        if value is not None:
            set_args[name] = value

    config_path = args['config_path']
    if config_path is None:
        config_path = "%s/settings.cfg" % script_dir

    try:
        config = get_config_values(config_path, defaults)
    except ValueError as e:
        print "Configuration error: %s" % e
        print 'Exiting...'
        exit()

    settings = config.copy()
    settings.update(set_args)

    settings['download_dir'] = os.path.expanduser(settings['download_dir'])
    settings['config_path'] = config_path

    if ('list_file' not in set_args) and ('list_file' not in config):
        settings['list_file'] = os.path.join(
            settings['download_dir'],
            'download_list.txt'
        )

    settings['list_file'] = os.path.expanduser(settings['list_file'])

    # Validate the settings
    settings_error = False
    if settings['resolution'] not in valid_resolutions:
        res_string = ', '.join(valid_resolutions)
        print "Configuration error: Invalid resolution. Valid values: %s" % res_string
        settings_error = True

    if not os.path.exists(settings['download_dir']):
        print 'Configuration error: The download directory must be a valid path'
        settings_error = True

    if settings['video_types'] not in valid_video_types:
        types_string = ', '.join(valid_video_types)
        print "Configuration error: Invalid video type. Valid values: %s" % types_string
        settings_error = True

    if settings['output_level'] not in valid_output_levels:
        output_string = ', '.join(valid_output_levels)
        print "Configuration error: Invalid output level. Valid values: %s" % output_string
        settings_error = True

    if not os.path.exists(os.path.dirname(settings['list_file'])):
        print 'Configuration error: the list file directory must be a valid path'
        settings_error = True

    if settings_error:
        print 'Exiting...'
        exit()

    return settings


def configure_logging(output_level):
    loglevel = 'DEBUG'
    if output_level == 'downloads':
        loglevel = 'INFO'
    elif output_level == 'error':
        loglevel = 'ERROR'

    numeric_level = getattr(logging, loglevel, None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % loglevel)
    logging.basicConfig(format='%(message)s', level=loglevel)


def convert_to_unicode(obj, encoding='utf-8'):
    if isinstance(obj, basestring):
        if not isinstance(obj, unicode):
            obj = unicode(obj, encoding)
    return obj


def main():
    settings = get_settings()
    configure_logging(settings['output_level'])

    logging.debug("Using configuration values:")
    logging.debug("Loaded configuration from %s" % settings['config_path'])
    for name in sorted(settings):
        if name != 'config_path':
            logging.debug("    {}: {}".format(name, settings[name]))

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
        # Use the "Just Added" JSON file
        newest_trailers = json.load(urllib.urlopen('http://trailers.apple.com/trailers/home/feeds/just_added.json'))

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
