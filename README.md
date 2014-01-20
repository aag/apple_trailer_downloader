Apple Trailers Downloader
=========================
This is a Python script to download HD trailers from the Apple Trailers website.
It uses the "Just Added" JSON file that is also used by the web interface to
find new trailers and keeps track of the ones it has already downloaded so
they aren't re-downloaded.

Dependencies
------------
The script depends on the following imports:

* Beautiful Soup 4 (http://www.crummy.com/software/BeautifulSoup/)

You can install Beautiful Soup with pip:

```
$ pip install beautifulsoup4
```

Using
-----
To download all the "Just Added" trailers in 720p into the script directory,
run:

```
$ python download_trailers.py
```

You can also download a specific trailer by passing the URL of the trailer's
page on the Apple Trailers site with the `-u` parameter.  For example:

```
$ python download_trailers.py -u "http://trailers.apple.com/trailers/lions_gate/thehungergames/"
```

Configuration
-------------
You can customize the resolution and download directory if you want.  Copy
`settings-example.cfg` to `settings.cfg` and change the values in it.

The script stores a list of files it has already downloaded in the download
directory, in the file `download_list.txt`.  Any trailer file listed
in the download list will not be re-downloaded, even if the trailer file
has already been deleted.  This allows you to delete trailers after you've
watched them, but still run the script on a regular basis and only download
trailers you've never seen before.

License
-------
This code is free software licensed under the GPL v3.  See the COPYING file
for details.
