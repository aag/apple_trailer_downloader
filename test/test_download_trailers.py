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

sys.path.append(path.dirname(path.dirname(path.abspath(__file__))))

import download_trailers as trailers


def test_map_res_to_apple_size_480():
    assert trailers.map_res_to_apple_size('480') == 'sd'


def test_map_res_to_apple_size_720():
    assert trailers.map_res_to_apple_size('720') == 'hd720'


def test_map_res_to_apple_size_1080():
    assert trailers.map_res_to_apple_size('1080') == 'hd1080'
