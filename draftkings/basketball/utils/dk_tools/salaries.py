"""
Contains classes to help manage the CSV contest files that draftkings gives out.
"""

import csv
import os
import re
from datetime import datetime

from django.conf import settings

from basketball.constants import PLAYER_MAP, TEAM_MAP

SALARIES_FOLDER = os.path.join(settings.BASE_DIR,  'basketball', 'fixtures', 'dk_salaries')


class PlayerSalary(object):
    """
    Represents am NBA player from the csv salary file provided by DraftKings.
    """
    def __init__(self):
        self.position = ''
        self.name = ''
        self.salary = 0
        self.opponent = ''


class SalaryFile(object):
    """Class that represents a draftking salary file.

    Provides a way to easily retrieve information from a particular salary file.
    """

    def __init__(self, file_name):
        """
        Args:
            file_name: name of the file (e.g. `03-26-2016.csv`)
        """
        assert re.match('(\d{2}-\d{2}-\d{4}\.csv)', file_name) is not None
        self.file_name = file_name

    def _full_path(self):
        """Full path to the file *relative* to this folder lol"""
        return os.path.join(SALARIES_FOLDER, self.file_name)

    def date(self):
        """converts the CSV file's name into a date object"""
        return datetime.strptime(self.file_name, '%m-%d-%Y.csv')

    def player_salaries(self):
        """Returns a list of `PlayerSalary`s from the contest"""
        return SalaryFileManager.salary_file_info(path=self._full_path())

    def __str__(self):
        return self.file_name


class SalaryFileManager(object):

    @classmethod
    def salary_files(cls):
        file_names = filter(
            lambda k: re.match('(\d{2}-\d{2}-\d{4}\.csv)', k),
            os.listdir(SALARIES_FOLDER))
        file_names.sort()
        return [SalaryFile(name) for name in file_names]

    @classmethod
    def salary_file_info(cls, file_obj=None, path=None):
        """
        Given a draft king contest csv file return a list of PlayerSalary
        """
        if file_obj is None and path is None:
            raise ValueError('You must supply either a file object or a path to a file.')

        def _get_info(file_obj):
            """Returns a list of `SalaryObject`s from the contest CSV file."""
            reader = csv.DictReader(file_obj, dialect=SalaryFileDialect)
            all_players = []
            for row in reader:
                # Figure out the teams
                teams_playing = row['GameInfo'].upper().split(' ')[0].split('@')
                teams_playing = [TEAM_MAP.get(t, t) for t in teams_playing]
                current_players_team = row['teamAbbrev'].upper()

                # Make the PlayerSalary
                player = PlayerSalary()
                player.position = row['Position']
                player.name = PLAYER_MAP.get(row['Name'], row['Name'])
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
                return _get_info(f)
        elif file_obj:
            return _get_info(file_obj)


class SalaryFileDialect(csv.Dialect):
    """The "Dialect" that the draftking contest CSV files use."""
    delimiter = ','
    quotechar = '"'
    doublequote = True
    skipinitialspace = True
    lineterminator = '\r\n'
    quoting = csv.QUOTE_MINIMAL
