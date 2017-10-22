Apple Trailers Downloader
=========================
[![Build Status](https://travis-ci.org/aag/apple_trailer_downloader.svg?branch=master)](https://travis-ci.org/aag/apple_trailer_downloader) [![License](https://img.shields.io/badge/License-GPLv3-blue.svg)](COPYING)

This is a Python script to download HD trailers from the Apple Trailers website.
It uses the "Just Added" JSON file that is also used by the web interface to
find new trailers, and keeps track of the ones it has already downloaded so
they aren't re-downloaded.

Requirements
------------
Running this script requires Python 2.7 or Python 3.3+. If you don't currently have
Python installed on your computer, see the setup documentation for
[Python 2](https://docs.python.org/2/using/index.html) or
[Python 3](https://docs.python.org/3/using/index.html).


Installation
------------
The script consists of a single `.py` file that you can put anywhere on your computer.
First, download the most recent release from [the releases page](/aag/apple_trailer_downloader/releases).
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

License
-------
This code is free software licensed under the GPL v3.  See the [COPYING](COPYING) file
for details.
