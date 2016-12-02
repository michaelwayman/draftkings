import datetime
import re
import os
from itertools import chain
from os import path
import logging as log

import simplejson as json
import requests

from bs4 import BeautifulSoup
from django.conf import settings

from basketball.constants import PLAYER_MAP
from basketball.models import Player

STARTERS_FOLDER = path.join(settings.BASE_DIR, 'basketball', 'fixtures', 'starters')
ROTO_PLAYER_MAP = path.join(STARTERS_FOLDER, 'roto_player_ids.json')


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

    @classmethod
    def starters_file_for_date(cls, date):
        starter_file = filter(
            lambda k: k.date() == date,
            cls.starter_files())

        if starter_file:
            return starter_file[0]
        return None


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
            self._data['injured'] = set(PLAYER_MAP.get(p, p) for p in self._data['injured'])
            self._data['starters'] = set(PLAYER_MAP.get(p, p) for p in self._data['starters'])

            for name in chain(*self._data.values()):
                try:
                    Player.objects.get(name=name)
                except Player.DoesNotExist as ex:
                    log.error('Cannot find player {} in the database.'.format(name))
                    raise ex

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
    def pull_name_for_player_id(cls, player_id):

        url = 'http://www.rotowire.com/basketball/player.htm?id={}'.format(player_id)
        response = requests.get(url, headers=cls.headers)
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'html.parser')
        player_name = soup.select('div.mlb-player-nameteam h1')[0].text

        return player_name

    @classmethod
    def pull_data_from_roto(cls):
        if os.path.exists(ROTO_PLAYER_MAP):
            with open(ROTO_PLAYER_MAP, 'r') as f:
                player_id_map = json.loads(f.read())
                needs_saved = False
        else:
            player_id_map = {}
            needs_saved = True

        response = requests.get(cls.url, headers=cls.headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        starter_data = soup.find_all('a', href=has_player_href, title=has_title_attr)
        injured_data = soup.find_all('a', href=has_player_href, title=no_title)

        starter_ids = set(map(
            lambda x: re.findall('id=(\d+)$', x['href'])[0],
            starter_data))

        injured_ids = set(map(
            lambda x: re.findall('id=(\d+)$', x['href'])[0],
            injured_data))

        player_ids = starter_ids | injured_ids
        for pid in player_ids:
            if pid not in player_id_map:
                log.warning('Cannot find roto id "{}" in the player map file. '
                         'attempting to fetch player\'s name from roto.'.format(pid))
                player_id_map[pid] = cls.pull_name_for_player_id(pid)
                needs_saved = True

        for player_name in player_id_map.values():
            try:
                Player.objects.get(name=PLAYER_MAP.get(player_name, player_name))
            except Player.DoesNotExist:
                log.error('Cannot find roto player "{}" in the db.'.format(player_name))

        if needs_saved:
            with open(ROTO_PLAYER_MAP, 'w') as f:
                log.info('saving the player map file to disk.')
                f.write(json.dumps(player_id_map))
                log.info('done.')

        starters = map(lambda x: player_id_map[x], starter_ids)
        injured = map(lambda x: player_id_map[x], injured_ids)
        return starters, injured


def has_player_href(href):
    return href and re.compile('/basketball/player.htm\?').search(href)


def has_title_attr(title):
    return title and re.compile('\w').search(title)


def no_title(title):
    return not title
