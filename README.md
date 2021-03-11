Apple Trailer Downloader
========================
[![Build Status](https://github.com/aag/apple_trailer_downloader/actions/workflows/ci.yml/badge.svg)](https://github.com/aag/apple_trailer_downloader/actions) [![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](COPYING)

This is a Python script to download HD trailers from the Apple Trailers website.
It uses the "Just Added" JSON file that is also used by the web interface to
find new trailers, and keeps track of the ones it has already downloaded so
they aren't re-downloaded.

Requirements
------------
Running this script requires Python 2.7 or Python 3.5+. If you don't currently have
Python installed on your computer, see the setup documentation for
[Python 2](https://docs.python.org/2/using/index.html) or
[Python 3](https://docs.python.org/3/using/index.html).


Installation
------------
The script consists of a single `.py` file that you can put anywhere on your computer.
First, download the most recent release from [the releases page](https://github.com/aag/apple_trailer_downloader/releases).
Extract the files and either run the script from the extracted directory or copy the
`download_trailers.py` script to any location of your choosing.

Alternatively, if you're comfortable using git, you can clone the repository to your computer
and run the script from the git clone. 


Usage
-----
The downloader works as a command-line program without a graphical interface. To run it, you
run `download_trailers.py` from a terminal.

If you do not provide any command-line arguments, the script will download the first trailer
for each of the current "Just Added" films, in 720p resolution, into the same directory as
the python script. Just run:

```
$ python download_trailers.py
```

You can also download a single specific trailer by passing the URL of the trailer's
page on the Apple Trailers site with the `-u` parameter.  For example:

```
$ python download_trailers.py -u "http://trailers.apple.com/trailers/lions_gate/thehungergames/"
```

Configuration
-------------
You can customize several settings either with command-line
options or with a config file. To see all available command-line options,
run the script with the `--help` switch.

```
$ python download_trailers.py --help
```

You can also put settings in a config file. An example settings file,
`settings-example.cfg` is included with the script. By default, the script
first looks for a `settings.cfg` file in its directory, and if it doesn't find
one there, it looks for a file `.trailers.cfg` in the user's home directory.
Whichever one it finds first will be used as the configuration file. You can
copy `settings-example.cfg` to either `settings.cfg` or `.trailers.cfg` and
customize the values in it. Alternatively, you can use the `--config` option
to specify a path to a config file.

If a setting is specified in both the config file and a command-line option,
the command-line setting will override the setting in the config file.

The script stores a list of files it has already downloaded in in a text
file.  Any trailer listed in this file will not be re-downloaded,
even if the trailer file has already been deleted.  This allows you to delete
trailers after you've watched them, but still run the script on a regular
basis and only download trailers you've never seen before. By default the
script stores the download list in the file `download_list.txt` in the
download directory, but you can change the file location with the
`--listfile` command-line option or with the `list_file` option in the
config file.


Usage as a Python Library
-------------------------
If you want to download trailers in your own Python application, you can use
`download_trailers.py` as a library to make that easier. Note that since we
have not reached a 1.0 release, the API is not guaranteed to be stable.


Example:

```python
import download_trailers as trailers

hg_trailers = trailers.get_trailer_file_urls('http://trailers.apple.com/trailers/lions_gate/thehungergames/', '480', 'trailers')

for trailer in hg_trailers:
    filename = trailers.get_trailer_filename(trailer['title'], trailer['type'], trailer['res'])
    trailers.download_trailer_file(trailer['url'], '/tmp/', filename)
```


Development
-----------

### Tests

There is a test suite written with pytest. If you don't already have it installed,
you can install it with pip.

```
$ sudo pip install pytest
```

Or, for Python 3:

```
$ sudo pip3 install pytest
```

You can then run all the tests by running `pytest` in the top directory of the repository.
If you have both Python 2.7 and Python 3 installed, you can run the tests with
both versions with this command:

```
$ python -m pytest && python3 -m pytest
```

### Coding Style

The code in the script is written to follow
[the PEP8 style guide](https://www.python.org/dev/peps/pep-0008/).
Both pylint and flake8 are used to check the coding style. You can install
both with pip.

```
$ sudo pip install pylint
$ sudo pip install flake8
```

Or, for Python 3:

```
$ sudo pip3 install pylint
$ sudo pip3 install flake8
```

You can run the linters by running `pylint *.py` and `flake8 *.py` in the top
directory of the repository.
If you have both Python 2.7 and Python 3 installed, you can run the linters
with both versions with these commands:

```
$ python -m pylint *.py && python3 -m pylint *.py
$ python -m flake8 *.py && python3 -m flake8 *.py
```

License
-------
This code is free software licensed under the GPL v3.  See the [COPYING](COPYING) file
for details.
