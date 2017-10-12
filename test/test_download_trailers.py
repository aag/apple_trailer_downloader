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

import sys
from os import path

# Add the parent directory to the path so we can import the main script
sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))
import download_trailers as trailers


TEST_DIR = test_dir = path.dirname(path.abspath(__file__))


def test_map_res_to_apple_size_480():
    assert trailers.map_res_to_apple_size('480') == 'sd'


def test_map_res_to_apple_size_720():
    assert trailers.map_res_to_apple_size('720') == 'hd720'


def test_map_res_to_apple_size_1080():
    assert trailers.map_res_to_apple_size('1080') == 'hd1080'


def test_convert_to_unicode():
    assert trailers.convert_to_unicode('test') == u'test'


def test_convert_src_url_to_file_url():
    src_url = 'http://movietrailers.apple.com/movies/lionsgate/thehungergames/hungergames-tlr2_720p.mov'
    file_url = 'http://movietrailers.apple.com/movies/lionsgate/thehungergames/hungergames-tlr2_h720p.mov'
    assert trailers.convert_src_url_to_file_url(src_url, 720) == file_url


def test_should_download_file_all():
    assert trailers.should_download_file('all', '')
    assert trailers.should_download_file('all', 'The Making of Safe and Sound')
    assert trailers.should_download_file('all', 'Trailer')


def test_should_download_file_single_trailer_trailer():
    assert trailers.should_download_file('single_trailer', 'Trailer')


def test_should_download_file_single_trailer_non_trailer():
    assert not trailers.should_download_file('single_trailer', '')
    assert not trailers.should_download_file('single_trailer', 'Clip')
    assert not trailers.should_download_file('single_trailer', 'Sneak Peek')
    assert not trailers.should_download_file('single_trailer', 'Trailer 2')


def test_should_download_file_trailers_trailers():
    assert trailers.should_download_file('trailers', 'Trailer')
    assert trailers.should_download_file('trailers', 'Trailer 2')
    assert trailers.should_download_file('trailers', 'Teaser')
    assert trailers.should_download_file('trailers', 'Teaser 2')
    assert trailers.should_download_file('trailers', 'First Look')


def test_should_download_file_trailers_non_trailers():
    assert not trailers.should_download_file('trailers', 'Clip')
    assert not trailers.should_download_file('trailers', 'Sneak Peek')
    assert not trailers.should_download_file('trailers', 'The Making of Safe and Sound')


def test_get_downloaded_files_missing_file():
    assert trailers.get_downloaded_files('/not/a/real/path/to/file.txt') == []


def test_get_downloaded_files_existing_file():
    list_file_path = path.join(TEST_DIR, 'fixtures', 'download_list.txt')
    download_list = [u'Film.Trailer 2.1080p.mov', u'☃.Clip.480p.mov']
    assert trailers.get_downloaded_files(list_file_path) == download_list
