<img src="http://i.imgur.com/iH2jdhV.png" align="right" />

Instagram Scraper
=================
[![Build Status](https://travis-ci.org/rarcega/instagram-scraper.svg?branch=master)](https://travis-ci.org/rarcega/instagram-scraper)

instagram-scraper is a command-line application written in Python that scrapes and downloads an instagram user's photos and videos. Use responsibly.

Install
-------
To install the project dependencies:
```bash
$ pip install -r requirements.txt
```

Usage
-----
To scrape a public user's media:
```bash
$ python app.py -u <username>             
```
-----

To scrape a list of user's media and the info associated with it:
```bash
$ python app.py -p path/to/profile_file.txt            
```

This will generate a csv file with info of the media with the following columns:
Account = account name
Likes = how many likes on this image
Posted = date posted (ie, now, 1d, 3w)
URL = direct url to img (on instagram)
Img = name of the image when saved in a folder
Hashtags = the hashtags from the firsts comments of this image

The name of the deffault csv file is created with the current date with this format: results-year-month-day.csv.
You can also specify the results output with:

```bash
$ python app.py -p /path/to/profile_txt_file -r /parh/to/csv_file            
```

To specify the download destination:
```bash
$ python app.py <username> -d /path/to/destination
```

To scrape a private user's media when you are an approved follower:
```bash
$ python app.py <username> -a <your username> -w <your password>
```

This are the deffault values for the instagramScraper:
If nor a username or a profile file is introduced the usernames will be retrieved from *`<current working directory>/<profiles.txt>`*
media folder is *`<current working directory>/<photos>/<username>`*
csv file is *`<current working directory>/<results-year-month-day.csv>`*
username and password is none (you will scrap as an anonymous user. You won't be capable of scraping private profiles)

So if you just use the following command you will use the all the deffault values:
```bash
$ python app.py
```

Contributing
------------

1. Check the open issues or open a new issue to start a discussion around
   your feature idea or the bug you found
2. Fork the repository, make your changes, and add yourself to [AUTHORS.md](AUTHORS.md)
3. Send a pull request

License
-------
This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
