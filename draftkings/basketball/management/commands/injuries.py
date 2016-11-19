
from django.core.management.base import BaseCommand

import unicodedata

from bs4 import BeautifulSoup
import requests
import re
from collections import namedtuple

from basketball.models import Player

Injury = namedtuple(
    'Injury', (
        'date',
        'player',
        'position',
        'injury',
        'expected_return'))


class Command(BaseCommand):

    help = 'Command to print a list of all the currently injured players.'

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):

        # CBS seems to be as updated as ESPN but better structured for scraping
        response = requests.get('http://www.cbssports.com/nba/injuries')

        # Get the table rows with the injury data
        soup = BeautifulSoup(response.content, 'html.parser')
        trs = soup.find_all(name='tr', class_=re.compile('row'))

        # Create a list of Injury objects from the table rows
        injuries = []
        for row in trs:
            r = [unicodedata.normalize("NFKD", _) for _ in list(row.strings)]  # Replace non breaking space characters with ascii
            if len(r) == 5:
                r[1] = PLAYER_MAP.get(r[1], r[1])  # Replace CBS player name to what's in the db
                injuries.append(
                    Injury(*r))

        # Add all the player names to a set
        # Print the players from CBS that we can't find in the database so we can add them to the PLAYER_MAP
        injured_players = set()
        for injury in injuries:
            try:
                Player.objects.get(name=injury.player)
                injured_players.add(injury.player)
            except Player.DoesNotExist:
                print('Cannot find player with name "{}"'.format(injury.player))

        print(injured_players)


PLAYER_MAP = {
    'J.R. Smith': 'JR Smith',
    'DeWayne Dedmon': 'Dewayne Dedmon',
    'J.J. Barea': 'Jose Juan Barea',
    ' Nene': 'Nene',
}
