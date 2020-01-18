# -*- coding: utf-8 -*-

"""This script contains tests for the Apple Trailers Downloader script.
"""

# Started on: 10.10.2017
#
# Copyright 2017 Adam Goforth
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

import copy
import logging
import os
import pytest
import shutil
import sys
import tempfile

# Add the parent directory to the path so we can import the main script
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import download_trailers as trailers

try:
    # For Python 2
    from ConfigParser import MissingSectionHeaderError
    from ConfigParser import Error
except ImportError:
    # For Python 3.0 and later
    from configparser import MissingSectionHeaderError
    from configparser import Error

TEST_DIR = test_dir = os.path.dirname(os.path.abspath(__file__))
DOWNLOAD_LIST_FIXTURE_PATH = os.path.join(TEST_DIR, 'fixtures', 'download_list.txt')

SOME_CONFIG_DEFAULTS = {
    'download_dir': '/tmp/download',
    'output_level': 'debug',
    'resolution': '720',
    'video_types': 'single_trailer',
}

SOME_VALID_SETTINGS = {
    'download_dir': '/',
    'list_file': '/list.txt',
    'output_level': 'error',
    'resolution': '1080',
    'video_types': 'trailers',
}

REQUIRED_SETTINGS = ['resolution', 'download_dir', 'video_types', 'output_level', 'list_file']


def test_map_res_to_apple_size_480():
    assert trailers.map_res_to_apple_size('480') == u'sd'


def test_map_res_to_apple_size_720():
    assert trailers.map_res_to_apple_size('720') == u'hd720'


def test_map_res_to_apple_size_1080():
    assert trailers.map_res_to_apple_size('1080') == u'hd1080'


def test_convert_src_url_to_file_url():
    src_url = 'http://movietrailers.apple.com/movies/lionsgate/thehungergames/hungergames-tlr2_720p.mov'
    file_url = 'http://movietrailers.apple.com/movies/lionsgate/thehungergames/hungergames-tlr2_h720p.mov'
    assert trailers.convert_src_url_to_file_url(src_url, 720) == file_url


def test_should_download_file_all():
    assert trailers.should_download_file('all', '')
    assert trailers.should_download_file('ALL', u'The Making of Safe and Sound')
    assert trailers.should_download_file('all', u'Trailer')
    assert trailers.should_download_file('all', u'Trailer ')


def test_should_download_file_single_trailer_trailer():
    assert trailers.should_download_file('single_trailer', u'Trailer')
    assert trailers.should_download_file('single_trailer', u'Trailer ')
    assert trailers.should_download_file('single_trailer', u'Trailer 1')
    assert trailers.should_download_file('single_trailer', u' Trailer 1 ')
    assert trailers.should_download_file('single_trailer', u' Trailer    1 ')


def test_should_download_file_single_trailer_non_trailer():
    assert not trailers.should_download_file('single_trailer', u'')
    assert not trailers.should_download_file('SINGLE_TRAILER', u'Clip')
    assert not trailers.should_download_file('Single_Trailer', u'Sneak Peek')
    assert not trailers.should_download_file('single_trailer', u'Trailer 2')


def test_should_download_file_trailers_trailers():
    assert trailers.should_download_file('trailers', u'Trailer')
    assert trailers.should_download_file('trailers', u'Trailer ')
    assert trailers.should_download_file('Trailers', u'Trailer 2 ')
    assert trailers.should_download_file('TRAILERS', u'Teaser')
    assert trailers.should_download_file('trailers', u'Teaser 2')
    assert trailers.should_download_file('trailers', u'First Look')


def test_should_download_file_trailers_non_trailers():
    assert not trailers.should_download_file('trailers', u'Clip')
    assert not trailers.should_download_file('TRAILERS', u'Sneak Peek')
    assert not trailers.should_download_file('Trailers', u'The Making of Safe and Sound')


def test_get_downloaded_files_missing_file():
    assert trailers.get_downloaded_files('/not/a/real/path/to/file.txt') == []


def test_get_downloaded_files_existing_file():
    download_list = [u'Film.Trailer 2.1080p.mov', u'☃.Clip.480p.mov']
    assert trailers.get_downloaded_files(DOWNLOAD_LIST_FIXTURE_PATH) == download_list


def test_write_downloaded_files_new_file():
    tmp_file, tmp_file_path = tempfile.mkstemp()
    os.close(tmp_file)

    trailers.write_downloaded_files([u'Film 1.Trailer 2.1080p.mov', u'Film2.mov'], tmp_file_path)

    assert trailers.get_downloaded_files(tmp_file_path) == [u'Film 1.Trailer 2.1080p.mov', u'Film2.mov']
    os.remove(tmp_file_path)


def test_write_downloaded_files_existing_file():
    tmp_file, tmp_file_path = tempfile.mkstemp()
    os.close(tmp_file)
    shutil.copyfile(DOWNLOAD_LIST_FIXTURE_PATH, tmp_file_path)

    trailers.write_downloaded_files([u'♪.Trailer.1080p.mov'], tmp_file_path)

    assert trailers.get_downloaded_files(tmp_file_path) == [u'♪.Trailer.1080p.mov']
    os.remove(tmp_file_path)


def test_record_downloaded_file_new_file():
    tmp_file, tmp_file_path = tempfile.mkstemp()
    os.close(tmp_file)

    trailers.record_downloaded_file(u'✓.Trailer.mov', tmp_file_path)

    assert trailers.get_downloaded_files(tmp_file_path) == [u'✓.Trailer.mov']
    os.remove(tmp_file_path)


def test_record_downloaded_file_existing_file():
    tmp_file, tmp_file_path = tempfile.mkstemp()
    os.close(tmp_file)
    shutil.copyfile(DOWNLOAD_LIST_FIXTURE_PATH, tmp_file_path)
    full_downloaded_list = [u'Film.Trailer 2.1080p.mov', u'☃.Clip.480p.mov', u'⚡.mov']

    trailers.record_downloaded_file(u'⚡.mov', tmp_file_path)

    assert trailers.get_downloaded_files(tmp_file_path) == full_downloaded_list
    os.remove(tmp_file_path)


def test_get_trailer_filename_simple():
    filename = u'The Hunger Games.Trailer.1080p.mov'
    assert trailers.get_trailer_filename(u'The Hunger Games', u'Trailer', u'1080') == filename


def test_get_trailer_filename_unicode():
    filename = u'★ Mötley Crüe ★.Clip 2.480p.mov'
    assert trailers.get_trailer_filename(u'★ Mötley Crüe ★', u'Clip 2', u'480') == filename


def test_get_trailer_filename_blacklist_chars():
    filename = u'Sophies Choice 1.Clip 2.480p.mov'
    assert trailers.get_trailer_filename(u'Sophie\'s Choice: 1 + ? = ?', u'Clip 2', u'480') == filename


def test_get_trailer_filename_repeating_spaces():
    filename = u'Film Movie.First Look.720p.mov'
    assert trailers.get_trailer_filename(u'  Film    :   + ?/= ?   Movie', u'First Look', u'720') == filename


def test_get_config_values_no_config_file():
    missing_file_path = '/not/a/path/on/any/real/system/settings.cfg'
    settings = copy.deepcopy(SOME_CONFIG_DEFAULTS)
    settings['download_all_urls'] = []

    assert trailers.get_config_values(missing_file_path, SOME_CONFIG_DEFAULTS) == settings


def test_get_config_values_empty_config_file():
    empty_config_file = os.path.join(TEST_DIR, 'fixtures', 'settings', 'empty_settings.cfg')
    settings = copy.deepcopy(SOME_CONFIG_DEFAULTS)
    settings['download_all_urls'] = []

    assert trailers.get_config_values(empty_config_file, SOME_CONFIG_DEFAULTS) == settings


def test_get_config_values_normal_config_file():
    empty_config_file = os.path.join(TEST_DIR, 'fixtures', 'settings', 'normal_settings.cfg')
    config_values = {
        'download_dir': '~/Videos/trailers',
        'list_file': '~/Videos/download_list.txt',
        'resolution': '1080',
        'video_types': 'all',
        'output_level': 'error',
        'download_all_urls': [
            '/trailers/one',
            '/trailers/two',
        ]
    }

    assert trailers.get_config_values(empty_config_file, SOME_CONFIG_DEFAULTS) == config_values


def test_get_config_values_missing_header_config_file():
    with pytest.raises(MissingSectionHeaderError):
        missing_header_config_file = os.path.join(TEST_DIR, 'fixtures', 'settings', 'no_header_settings.cfg')
    
        trailers.get_config_values(missing_header_config_file, SOME_CONFIG_DEFAULTS)


def test_get_config_values_missing_values_config_file():
    with pytest.raises(Error):
        unparsable_config_file = os.path.join(TEST_DIR, 'fixtures', 'settings', 'unparsable_settings.cfg')

        trailers.get_config_values(unparsable_config_file, SOME_CONFIG_DEFAULTS)


def test_configure_logging_default():
    trailers.configure_logging('')
    assert logging.root.getEffectiveLevel() == logging.DEBUG


def test_configure_logging_invalid_level():
    trailers.configure_logging('not a real log level')
    assert logging.root.getEffectiveLevel() == logging.DEBUG


def test_configure_logging_downloads():
    trailers.configure_logging('downloads')
    assert logging.root.getEffectiveLevel() == logging.INFO


def test_configure_logging_error():
    trailers.configure_logging('error')
    assert logging.root.getEffectiveLevel() == logging.ERROR


def test_validate_settings_resolution_valid():
    settings = copy.deepcopy(SOME_VALID_SETTINGS)
    for resolution in ['480', '720', '1080']:
        settings['resolution'] = resolution
        assert trailers.validate_settings(settings)


def test_validate_settings_invalid_resolutions():
    settings = copy.deepcopy(SOME_VALID_SETTINGS)
    for resolution in ['', '48', '7200', '1080p', '4k']:
        with pytest.raises(ValueError):
            settings['resolution'] = resolution
            assert trailers.validate_settings(settings)


def test_validate_settings_download_dir_valid():
    settings = copy.deepcopy(SOME_VALID_SETTINGS)
    existing_dir_path = tempfile.mkdtemp()

    settings['download_dir'] = existing_dir_path
    assert trailers.validate_settings(settings)

    os.rmdir(existing_dir_path)


def test_validate_settings_invalid_download_dir():
    settings = copy.deepcopy(SOME_VALID_SETTINGS)
    for path in ['', '/not/a/valid/path', '~', '~/']:
        with pytest.raises(ValueError):
            settings['download_dir'] = path
            assert trailers.validate_settings(settings)


def test_validate_settings_video_types_valid():
    settings = copy.deepcopy(SOME_VALID_SETTINGS)
    for video_type in ['single_trailer', 'trailers', 'all', 'All', 'ALL']:
        settings['video_type'] = video_type
        assert trailers.validate_settings(settings)


def test_validate_settings_invalid_video_types():
    settings = copy.deepcopy(SOME_VALID_SETTINGS)
    for video_types in ['', 'trailer', 'single-trailer', 'everything', '*']:
        with pytest.raises(ValueError):
            settings['video_types'] = video_types
            assert trailers.validate_settings(settings)


def test_validate_settings_output_level_valid():
    settings = copy.deepcopy(SOME_VALID_SETTINGS)
    for output_level in ['debug', 'downloads', 'error', 'ERROR', 'Error']:
        settings['output_level'] = output_level
        assert trailers.validate_settings(settings)


def test_validate_settings_invalid_output_level():
    settings = copy.deepcopy(SOME_VALID_SETTINGS)
    for output_level in ['', 'download', 'errors', '*', 'all']:
        with pytest.raises(ValueError):
            settings['output_level'] = output_level
            assert trailers.validate_settings(settings)


def test_validate_settings_list_file_valid():
    settings = copy.deepcopy(SOME_VALID_SETTINGS)
    existing_file_path = tempfile.NamedTemporaryFile().name

    settings['list_file'] = existing_file_path
    assert trailers.validate_settings(settings)


def test_validate_settings_invalid_list_file():
    with pytest.raises(ValueError):
        settings = copy.deepcopy(SOME_VALID_SETTINGS)
        missing_file_path = '/not/a/valid/path/on/any/real/system/list.txt'

        settings['list_file'] = missing_file_path
        assert trailers.validate_settings(settings)


def test_validate_settings_setting_missing():
    for setting in REQUIRED_SETTINGS:
        with pytest.raises(ValueError):
            settings = copy.deepcopy(SOME_VALID_SETTINGS)
            settings.pop(setting)
            trailers.validate_settings(settings)


def test_clean_url_with_traling_slash():
    orig_url = "https://trailers.apple.com/path/film/"

    assert trailers.get_url_path(orig_url) == "/path/film"


def test_clean_url_without_trailing_slash():
    orig_url = "https://trailers.apple.com/path/film"

    assert trailers.get_url_path(orig_url) == "/path/film"

# def test_get_trailer_file_urls_invalid_domain():
#     urls = trailers.get_trailer_file_urls("http://www.Norkm3cHedUNPmL7vMALFaYUp4o7jcLF9KTmwTAMPzNNoyxp.com/test", "480", ["all"], [])
#     assert not urls

# def test_get_trailer_file_urls_invalid_response():
#     urls = trailers.get_trailer_file_urls("http://www.example.com/test", "480", ["all"], [])
#     assert not urls

# def test_get_trailer_file_urls_404():
#     urls = trailers.get_trailer_file_urls("https://definingterms.com/random_url_XHNcTCAwihjCRoxV7igg9gwk", "480", ["all"], [])
#     assert not urls

