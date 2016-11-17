"""
Contains classes to help manage the CSV contest files that draftkings gives out.
"""

import csv
import os
import re
from datetime import datetime


CONTEST_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'fixtures', 'dk_salaries')


class ContestPlayer(object):
    """
    Represents am NBA player from the csv contest file provided by DraftKings.
    """
    def __init__(self):
        self.position = ''
        self.name = ''
        self.salary = 0
        self.opponent = ''


class Contest(object):
    """Class that represents a draftkings contest as provided by a CSV file.

    Provides a way to easily retrieve information from a particular contest file.
    """

    def __init__(self, file_name):
        """
        Args:
            file_name: name of the file (e.g. `03-26-2016.csv`)
        """
        assert re.match('(\d{2}-\d{2}-\d{4}\.csv)', file_name) is not None
        self.file_name = file_name

    def full_path(self):
        """Full path to the file *relative* to this folder lol"""
        return os.path.join(CONTEST_FOLDER, self.file_name)

    def date(self):
        """converts the CSV file's name into a date object"""
        return datetime.strptime(self.file_name, '%m-%d-%Y.csv')

    def players(self):
        """Returns a list of `ContestPlayer`s from the contest"""
        return CSVManager.contest_player_info(path=self.full_path())

    def __str__(self):
        return self.file_name


class CSVManager(object):

    @classmethod
    def contests(cls):
        file_names = filter(
            lambda k: re.match('(\d{2}-\d{2}-\d{4}\.csv)', k),
            os.listdir(CONTEST_FOLDER))
        file_names.sort()
        return [Contest(name) for name in file_names]

    @classmethod
    def contest_player_info(cls, file_obj=None, path=None):
        """
        Given a draft king contest csv file return a list of ContestPlayer objects
        """

        def _get_player_info(file_obj):
            """Returns a list of `ContestPlayer`s from the contest CSV file."""
            reader = csv.DictReader(file_obj, dialect=DKDialect)
            all_players = []
            for row in reader:
                # Figure out the teams
                teams_playing = row['GameInfo'].upper().split(' ')[0].split('@')
                teams_playing = [TEAM_MAP.get(t, t) for t in teams_playing]
                current_players_team = row['teamAbbrev'].upper()

                # Make the ContestPlayer
                player = ContestPlayer()
                player.position = row['Position']
                player.name = PLAYER_NAME_MAP.get(row['Name'], row['Name'])
                player.salary = int(row['Salary'])
                # Figure out the opponent
                if teams_playing[0] == current_players_team:
                    player.opponent = teams_playing[1]
                else:
                    player.opponent = teams_playing[0]

                all_players.append(player)

            return all_players

        # Figure out whether we were passed a file or a path to a file.
        if path:
            with open(path) as f:
                return _get_player_info(f)
        elif file_obj:
            return _get_player_info(file_obj)
        else:
            raise ValueError('You must supply either a file object or a path to a file.')


class DKDialect(csv.Dialect):
    """The "Dialect" that the draftking contest CSV files use."""
    delimiter = ','
    quotechar = '"'
    doublequote = True
    skipinitialspace = True
    lineterminator = '\r\n'
    quoting = csv.QUOTE_MINIMAL


# Map CSV file team abbreviations to names used in the database
TEAM_MAP = {
    'NY': 'NYK',
    'NO': 'NOP',
    'PHO': 'PHX',
    'SA': 'SAS',
}

# Map CSV file player name's to names used in the database
PLAYER_NAME_MAP = {
    'C.J. McCollum': 'CJ McCollum',
    'J.J. Redick': 'JJ Redick',
    'J.J. Barea': 'Jose Juan Barea',
    'C.J. Watson': 'CJ Watson',
    'T.J. McConnell': 'TJ McConnell',
    'Louis Amundson': 'Lou Amundson',
    'Luc Richard Mbah a Moute': 'Luc Mbah a Moute',
    'C.J. Wilcox': 'CJ Wilcox',
    'R.J. Hunter': 'RJ Hunter',
    'J.J. Hickson': 'JJ Hickson',
    'P.J. Hairston': 'PJ Hairston',
    'T.J. Warren': 'TJ Warren',
    'P.J. Tucker': 'PJ Tucker',
    'Kelly Oubre Jr.': 'Kelly Oubre',
    'K.J. McDaniels': 'KJ McDaniels',
    'C.J. Miles': 'CJ Miles',
    'Glenn Robinson III': 'Glenn Robinson',
    'Jakarr Sampson': 'JaKarr Sampson',
    'Nene Hilario': 'Nene',
    'Timothe Luwawu-Cabarrot': 'Timothe Luwawu',
    'Wade Baldwin IV': 'Wade Baldwin',
    'A.J. Hammons': 'AJ Hammons',
    'Guillermo Hernangomez': 'Willy Hernangomez',
    'Stephen Zimmerman Jr.': 'Stephen Zimmerman',
    'DeAndre\' Bembry': 'DeAndre Bembry',
    'J.R. Smith': 'JR Smith',
}
