"""
Contains classes to help manage the CSV contest files that draftkings gives out.
"""

import csv
import logging as log
import os
import re
from datetime import datetime

from django.conf import settings

from basketball.constants import PLAYER_MAP, TEAM_MAP
from basketball.models import Player, GameLog

SALARIES_FOLDER = os.path.join(settings.BASE_DIR,  'basketball', 'fixtures', 'salaries')


class PlayerSalary(object):
    """
    Represents am NBA player from the csv salary file provided by DraftKings.
    """
    def __init__(self, name=None, position=None, salary=None, opponent=None):
        self.position = position
        self.name = name
        self.salary = salary
        self.opponent = opponent


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
        """
        Returns:
            Full path to the file *relative* to this folder lol"""
        return os.path.join(SALARIES_FOLDER, self.file_name)

    def date(self):
        """
        Returns:
            a date object from the CSV file's name"""
        return datetime.strptime(self.file_name, '%m-%d-%Y.csv')

    def save_to_db(self):
        # for each player try to find their PlayerStat for a particular
        # game and update their salary to the database
        for player in self.player_salaries():

            # try to find the PlayerStat in the database and update the salary.
            try:
                p = Player.objects.get(name=player.name)
                game_log = GameLog.objects.get(player=p, game__date=self.date())
            except Player.DoesNotExist:
                log.error(
                    'Player {name} cannot be found.'.format(
                        name=player.name))
            except GameLog.DoesNotExist:
                log.warning(
                    'GameLog for {name} on {date} cannot be found.'.format(
                        name=player.name,
                        date=self.date()))
            else:
                game_log.dk_salary = player.salary
                game_log.save()

    def from_db(self):
        """
        Returns:
            a list of `models.Player` from the db with the salary attributes assigned"""
        retval = []
        player_salaries = self.player_salaries()
        players = Player.objects.filter(name__in=[ps.name for ps in player_salaries])
        for ps in player_salaries:
            p = players.get(name=ps.name)
            p.salary = ps.salary
            p.position = ps.position
            p.opponent = ps.opponent
            retval.append(p)
        return retval

    def player_salaries(self):
        """
        Returns:
             a list of `PlayerSalary`s
        """
        file_obj = open(self._full_path())
        reader = csv.DictReader(file_obj, dialect=SalaryFileDialect)
        all_players = []
        for row in reader:
            # Figure out the teams
            teams_playing = row['GameInfo'].upper().split(' ')[0].split('@')
            teams_playing = [TEAM_MAP.get(t, t) for t in teams_playing]
            current_players_team = row['teamAbbrev'].upper()
            if teams_playing[0] == current_players_team:
                opponent = teams_playing[1]
            else:
                opponent = teams_playing[0]

            # Make the PlayerSalary
            player = PlayerSalary(
                name=PLAYER_MAP.get(row['Name'], row['Name']),
                position=set(row['Position'].split('/')),
                salary=int(row['Salary']),
                opponent=opponent)

            all_players.append(player)

        return all_players

    def __str__(self):
        return self.file_name


class SalaryFileManager(object):

    @classmethod
    def salary_files(cls):
        """
        Returns:
             a list of the available `SalaryFile`s
        """
        file_names = filter(
            lambda k: re.match('(\d{2}-\d{2}-\d{4}\.csv)', k),
            os.listdir(SALARIES_FOLDER))
        file_names.sort()
        return [SalaryFile(name) for name in file_names]


class SalaryFileDialect(csv.Dialect):
    """The "Dialect" that the draftking contest CSV files use."""
    delimiter = ','
    quotechar = '"'
    doublequote = True
    skipinitialspace = True
    lineterminator = '\r\n'
    quoting = csv.QUOTE_MINIMAL
