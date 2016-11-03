#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Usage: 
python app.py <username>
"""

import argparse
import concurrent.futures
import errno
import json
import os
import re
import requests
import sys
import tqdm
import traceback
import warnings
import time
import csv
import datetime
import shutil
import humanize

warnings.filterwarnings('ignore')


class InstagramScraper:

    def __init__(self, login_user=None, login_pass=None, dst=None):
        self.base_url = 'https://www.instagram.com/'
        self.login_url = self.base_url + 'accounts/login/ajax/'
        self.logout_url = self.base_url + 'accounts/logout/'

        # Multithreads is used for downloading the images
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        self.future_to_item = {}

        if dst is not None:
            self.dst = dst
        else:
            self.dst = 'photos/'

        try:
            os.makedirs(self.dst)
        except OSError, e:
            if e.errno == errno.EEXIST and os.path.isdir(self.dst):
                # Directory already exists
                pass
            else:
                # Target dir exists as a file, or a different error
                raise

        # Creating the session
        self.session = requests.Session()
        self.csrf_token = None
        self.logged_in = False

        # If the user introduced a instagram account we log in
        if login_user and login_pass:
            self.login_user = login_user
            self.login_pass = login_pass
            self.login()

        
    def _epoch_to_string(self, epoch):
        ''' Auxiliar function to transform the date time epoch from instagram and to humanize
            the timedelta of it'''
        time_delta = datetime.datetime.now() - datetime.datetime.fromtimestamp(float(epoch))
        return humanize.naturaltime(time_delta)

    def login(self):
        self.session.headers.update({'Referer': self.base_url})
        req = self.session.get(self.base_url)

        self.session.headers.update({'X-CSRFToken': req.cookies['csrftoken']})

        login_data = {'username': self.login_user, 'password': self.login_pass}
        login = self.session.post(self.login_url, data=login_data, allow_redirects=True)
        self.session.headers.update({'X-CSRFToken': login.cookies['csrftoken']})
        self.csrf_token = login.cookies['csrftoken']

        if login.status_code == 200 and json.loads(login.text)['authenticated']:
            self.logged_in = True
        else:
            raise ValueError('Login failed for %s' % self.login_user)

    def logout(self):
        if self.logged_in:
            try:
                logout_data = {'csrfmiddlewaretoken': self.csrf_token}
                self.session.post(self.logout_url, data=logout_data)
                self.logged_in = False
            except:
                traceback.print_exc()

    def scrape(self, username, direct=None):
        """Crawls through and downloads user's media"""
        
        # Crawls the media and sends it to the executor.
        for item in tqdm.tqdm(self.media_gen(username), desc="Searching for %s media" % username, unit=" images"):
            # Creating the dict that countains the info that is going to be scraped
            photo = {}
            photo['Account'] = username
            photo['Likes'] = item['likes']['count']
            photo['Posted'] = self._epoch_to_string(item['created_time'])
            photo['URL'] = item[item['type'] + 's']['standard_resolution']['url'].split('?')[0]
            photo['Img'] = photo['URL'].split('/')[-1]
            # Hashtags
            photo['Hashtags'] = []
            # We look into the caption
            try:
                hashtags_caption = re.findall('(#[^\s]+)', item['caption']['text'])
            except TypeError:
                pass
            else:
                for hashtag in hashtags_caption:
                    if hashtag not in photo['Hashtags']:
                        photo['Hashtags'].append(hashtag.encode('utf8'))

            # We look into the comments
            if item['comments']['count'] > 0:
                for comment in item['comments']['data']:
                    hashtags = re.findall('(#[^\s]+)', comment['text'])
                    for hashtag in hashtags:
                        if hashtag not in photo['Hashtags']:
                            photo['Hashtags'].append(hashtag.encode('utf8'))
            
            # Joining the hashtags with a comma
            photo['Hashtags'] = ', '.join(photo['Hashtags'])

            future = self.executor.submit(self.download, item, photo['URL'], photo['Img'], username)
            self.future_to_item[future] = item

            # We return the info associated with the image that has been downloaded
            yield photo

        # Displays the progress bar of completed downloads. Might not even pop up if all media is downloaded while
        # the above loop finishes.
        for future in tqdm.tqdm(concurrent.futures.as_completed(scraper.future_to_item), total=len(scraper.future_to_item),
                                desc='Downloading %s' % username):
            item = scraper.future_to_item[future]

            if future.exception() is not None:
                print '%r generated an exception: %s' % (item['id'], future.exception())
    
    def scrape_profiles(self, usernames, direc=None):
        """ Scrapes a list of of profiles and save their media and info associated to it to a csv file """
        # We create a defect value for direc if it wasn't introduced
        if not direc:
            date = datetime.date.today()
            direc = 'results-%s-%s-%s.csv' % (date.year, date.month, date.day)
        # Creating or opening results csv.
        csv_file = open(direc, 'w')
        fieldnames = ['Account', 'Likes', 'Posted', 'URL', 'Img', 'Hashtags']
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()

        for username in usernames:
            # We create a folder for every user
            if not os.path.exists('%s/%s' % (self.dst, username)):
                os.makedirs('%s/%s' % (self.dst, username))

            for photo in self.scrape(username):
                writer.writerow(photo)
            print('%s has been scraped' % username)
        
        self.logout()
        csv_file.close()


    def media_gen(self, username):
        """Generator of all user's media"""

        media = self.fetch_media(username, max_id=None)
        while True:
            for item in media['items']:
                yield item
            if media.get('more_available') == True:
                max_id = media['items'][-1]['id']
                media = self.fetch_media(username, max_id)
            else:
                return

    def fetch_media(self, username, max_id):
        """Fetches the user's media metadata"""

        url = self.base_url + username + '/media'

        if max_id is not None:
            url += '?&max_id=' + max_id

        resp = self.session.get(url)

        if resp.status_code == 200:
            media = json.loads(resp.text)

            if not media['items']:
                self.logout()
                raise ValueError('User %s is private' % username)

            return media
        else:
            self.logout()
            raise ValueError('User %s does not exist' % username)

    def download(self, item, url, filename, username):
        """Downloads the media file"""

        # remove dimensions to get largest image
        url = re.sub(r'/s\d{3,}x\d{3,}/', '/', url)

        file_path = os.path.join(self.dst, username, filename)

        if not os.path.isfile(file_path):
            try:
                image = self.session.get(url, stream=True)
            except requests.exceptions.ConnectionError:
                time.sleep(5)
                image = requests.get(url, stream=True)
            
            with open(file_path, 'wb') as file:
                image.raw.decode_content = True
                shutil.copyfileobj(image.raw, file)

            file_time = int(item['created_time'])
            os.utime(file_path, (file_time, file_time))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="instagram-scraper scrapes and downloads an instagram user's photos and videos.")

    parser.add_argument('--username', '-u', help='Instagram user to scrape')
    parser.add_argument('--profiles', '-p', help='file txt with the profiles to scrap')
    parser.add_argument('--destination', '-d', help='Destination to download the media')
    parser.add_argument('--results', '-r', help='Csv file to store the media info')
    parser.add_argument('--login_user', '-a', help='Instagram login user')
    parser.add_argument('--login_pass', '-w', help='Instagram login password')

    args = parser.parse_args()

    if (args.login_user and args.login_pass is None) or (args.login_user is None and args.login_pass):
        parser.print_help()
        raise ValueError('Must provide login user AND password')

    if args.profiles:
        with open(args.profiles, 'r') as f:
            usernames = [line.rstrip('\n') for line in f]
            scraper = InstagramScraper(args.login_user, args.login_pass, args.destination)
            scraper.scrape_profiles(usernames, args.results)
    elif args.username:
        scraper = InstagramScraper(args.login_user, args.login_pass, args.destination)
        scraper.scrape(args.username)
    
    else:
        if os.path.isfile('profiles.txt'):
            with open('profiles.txt', 'r') as f:
                usernames = [line.rstrip('\n') for line in f]
                scraper = InstagramScraper(args.login_user, args.login_pass, args.destination)
                scraper.scrape_profiles(usernames, args.results)
        else:
            raise ValueError('Please provide a username or a txt file for the profiles')
        
            