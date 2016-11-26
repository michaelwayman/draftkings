import datetime
import re

import os
from os import path

import simplejson as json
import requests

from bs4 import BeautifulSoup
from django.conf import settings


STARTERS_FOLDER = path.join(settings.BASE_DIR, 'basketball', 'fixtures', 'starters')


class StartersFileManager(object):

    @classmethod
    def starter_files(cls):
        """
        Returns:
             a list of the available `StartersFile`s
        """
        file_names = filter(
            lambda k: re.match('(\d{2}-\d{2}-\d{4}\.json)', k),
            os.listdir(STARTERS_FOLDER))
        file_names.sort()
        return [StartersFile(name) for name in file_names]

    @classmethod
    def create_starters_file(cls, starters, injured, name):
        p = path.join(STARTERS_FOLDER, name)
        with open(p, 'w') as f:
            f.write(
                json.dumps({
                    'starters': starters,
                    'injured': injured}))


class StartersFile(object):

    def __init__(self, file_name):
        self.file_name = file_name
        self._data = None

    def __str__(self):
        return self.file_name

    def _full_path(self):
        """
        Returns:
            Full path to the file *relative* to this folder lol"""
        return os.path.join(STARTERS_FOLDER, self.file_name)

    def date(self):
        """
        Returns:
            a date object from the file's name"""
        return datetime.datetime.strptime(self.file_name, '%m-%d-%Y.json')

    def _read_file(self):
        with open(self._full_path(), 'r') as f:
            self._data = json.loads(f.read())

    def injured_players(self):
        if self._data is None:
            self._read_file()
        return self._data['injured']

    def starting_players(self):
        if self._data is None:
            self._read_file()
        return self._data['starters']


class RotoScraper(object):

    url = 'http://www.rotowire.com/basketball/nba_lineups.htm'
    headers = {'user-agent': 'Mozilla/4.1 (Macintosh; Intel Mac OS X 10_8_1)'}

    @classmethod
    def pull_data_from_roto(cls):
        response = requests.get(cls.url, headers=cls.headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        starter_data = soup.find_all('a', href=has_player_href, title=has_title_attr)
        injured_data = soup.find_all('a', href=has_player_href, title=no_title)

        starters = map(lambda x: x.text, starter_data)
        injured = map(lambda x: x.text, injured_data)

        return starters, injured


def has_player_href(href):
    return href and re.compile('/basketball/player.htm\?').search(href)


def has_title_attr(title):
    return title and re.compile('\w').search(title)


def no_title(title):
    return not title
