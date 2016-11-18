from __future__ import unicode_literals
import itertools

from datetime import datetime, timedelta
import six

from django.db import models
from django.db.models import Q
from django.conf import settings


class Season(models.Model):
    name_choices = (
        ('14', '14-15'),
        ('15', '15-16'),
        ('16', '16-17'),)

    name = models.CharField(max_length=2, choices=name_choices)
    scrape_id = models.IntegerField(null=True, blank=True, unique=True)

    def __str__(self):
        return self.scrape_string()

    def start_year(self):
        return 2000 + int(six.text_type(self.name))

    def end_year(self):
        return 2001 + int(six.text_type(self.name))

    def scrape_string(self):
        first_part = 2000 + int(six.text_type(self.name))
        second_part = int(six.text_type(self.name)) + 1
        return '-'.join([str(first_part), str(second_part)])

    def year_for_date(self, date):
        if date.month > 8:
            return 2000 + int(six.text_type(self.name))
        else:
            return 2001 + int(six.text_type(self.name))


class GameManager(models.Manager):

    def games_for_team(self, team):
        if isinstance(team, six.string_types):
            if len(team) <= 3:
                q = Q(away_team__short=team) | Q(home_team__short=team)
            else:
                q = Q(away_team__name=team) | Q(home_team__name=team)
        elif isinstance(team, Team):
            q = Q(away_team=team) | Q(home_team=team)
        else:
            q = Q(away_team__pk=team) | Q(home_team__pk=team)
        return self.filter(q).order_by('date')


class Game(models.Model):
    scrape_id = models.IntegerField(null=True, blank=True, unique=True)
    date = models.DateTimeField()
    season = models.ForeignKey('Season', related_name='games')
    home_team = models.ForeignKey('Team', related_name='home_games', null=True, blank=True)
    away_team = models.ForeignKey('Team', related_name='away_games', null=True, blank=True)
    home_elo = models.IntegerField(default=0)
    away_elo = models.IntegerField(default=0)
    elo_applied = models.BooleanField(default=False)

    objects = GameManager()

    def __str__(self):
        return '{teams} {date}'.format(
            teams='{} v {}'.format(self.home_team, self.away_team),
            date=self.date.date())

    def home_team_score(self):
        game_logs = GameLog.objects.filter(
            game=self,
            team=self.home_team)
        return sum(gl.points for gl in game_logs)

    def away_team_score(self):
        game_logs = GameLog.objects.filter(
            game=self,
            team=self.away_team)
        return sum(gl.points for gl in game_logs)

    def winner(self):
        if self.home_team_score() > self.away_team_score():
            return self.home_team
        else:
            return self.away_team

    def home_team_previous_game(self):
        return Game.objects.filter(
            home_team=self.home_team,
            date__lt=self.date).order_by('-date').first()

    def away_team_previous_game(self):
        return Game.objects.filter(
            home_team=self.home_team,
            date__lt=self.date).order_by('-date').first()

    def elo_for_team(self, team):
        if team.pk == self.home_team.pk:
            return self.home_elo
        return self.away_elo


class Team(models.Model):
    scrape_id = models.IntegerField(null=True, blank=True, unique=True)
    city = models.CharField(max_length=20)
    name = models.CharField(max_length=20, unique=True)
    abbreviation = models.CharField(max_length=4, unique=True)
    elo = models.IntegerField(default=1500)

    def set_of_all_players(self):
        return {gl.player for gl in GameLog.objects.filter(team=self)}

    def __str__(self):
        return self.name

    def average_points(self, game_logs=None):
        game_stats = self.game_logs_grouped_by_game(game_logs=game_logs)
        if len(game_stats):
            return sum(s.draft_king_points for s in itertools.chain(*game_stats)) / len(game_stats)
        return 0

    def average_playtime(self, game_logs=None):
        game_stats = self.game_logs_grouped_by_game(game_logs=game_logs)
        if len(game_stats):
            return sum(s.minutes for s in itertools.chain(*game_stats)) / len(game_stats)
        return 0

    def game_logs(self):
        return GameLog.objects.filter(team=self)

    def game_logs_grouped_by_game(self, game_logs=None):
        games = Game.objects.games_for_team(self)
        return_value = []
        for game in games:
            if game_logs is not None:
                team_game_logs = game_logs.filter(game=game, team=self)
            else:
                team_game_logs = GameLog.objects.filter(game=game, team=self)

            if team_game_logs:
                return_value.append(team_game_logs)

        return return_value


class Player(models.Model):
    scrape_id = models.IntegerField(null=True, blank=True, unique=True)

    name = models.CharField(max_length=40)
    current_team = models.ForeignKey('Team', related_name='players')
    games = models.ManyToManyField('Game', through='GameLog')

    position = models.CharField(max_length=2, null=True, blank=True)
    birthday = models.DateField(null=True, blank=True)
    weight = models.IntegerField(null=True, blank=True)  # kg
    height = models.IntegerField(null=True, blank=True)  # cm
    games_started = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def age(self):
        today = datetime.today()
        return today.year - self.birthday.year - ((today.month, today.day) < (self.birthday.month, self.birthday.day))

    def game_logs_since_date(self, date, from_date=None):
        if not from_date:
            from_date = datetime.now().date()

        return (
            self.gamelog_set
                .filter(game__date__gte=date)
                .filter(game__date__lte=from_date)
                .order_by('-game__date'))

    def game_logs_before_date(self, date):
        return (
            self.gamelog_set
                .filter(game__date__lte=date)
                .order_by('-game__date'))

    def game_logs_last_x_days(self, x, from_date=None):
        if not from_date:
            from_date = datetime.now().date()
        return self.game_logs_since_date(from_date - timedelta(days=x), from_date=from_date)

    def game_logs_last_x_games(self, x, from_date=None):
        if not from_date:
            from_date = datetime.now().date()
        return self.gamelog_set.filter(game__date__lte=from_date).order_by('-game__date')[:x]

    def game_logs_against_team(self, team):
        if isinstance(team, six.string_types):
            if len(team) <= 3:
                q = Q(game__away_team__short=team) | Q(game__home_team__short=team)
            else:
                q = Q(game__away_team__name=team) | Q(game__home_team__name=team)
        elif isinstance(team, Team):
            q = Q(game__away_team=team) | Q(game__home_team=team)
        else:
            q = Q(game__away_team__pk=team) | Q(game__home_team__pk=team)
        return self.gamelog_set.filter(q)

    def average_points(self, game_logs=None):
        game_logs = game_logs or self.gamelog_set.all()
        all_draft_king_points = [gl.draft_king_points for gl in game_logs]
        if all_draft_king_points:
            return round(sum(all_draft_king_points) / len(all_draft_king_points), 2)
        return 0

    def average_minutes(self, game_logs=None):
        game_logs = game_logs or self.gamelog_set.all()
        all_minutes = [gl.minutes for gl in game_logs]
        if all_minutes:
            return round(sum(all_minutes) / len(all_minutes), 2)
        return 0

    def average_ppm(self, game_logs=None):
        game_logs = game_logs or self.gamelog_set.all()
        avg_minutes = self.average_minutes(game_logs=game_logs)
        avg_points = self.average_points(game_logs=game_logs)
        if avg_minutes and avg_points:
            return round(avg_points / avg_minutes, 2)
        return 0

    def total_games_last_x_days(self, x):
        return len(self.stats_last_x_days(x))

    def game_logs_for_season(self, season):
        return GameLog.objects.filter(player=self, game__season=season)

    def estimated_points(self, opponent=None, date=None, salary=None):
        if date is None:
            date = datetime.now()
        game_logs_1 = self.game_logs_last_x_days(90, from_date=date - timedelta(days=1))
        game_logs_2 = self.game_logs_last_x_days(1, from_date=date - timedelta(days=1))

        return self.average_points(game_logs=game_logs_1) * 0.75 + self.average_points(game_logs=game_logs_1) * 0.25


class GameLog(models.Model):
    player = models.ForeignKey('Player')
    game = models.ForeignKey('Game')
    team = models.ForeignKey('Team')
    dk_salary = models.IntegerField(null=True, blank=True)

    minutes = models.IntegerField()
    offensive_rebounds = models.IntegerField()
    defensive_rebounds = models.IntegerField()
    personal_fouls = models.IntegerField()
    assists = models.IntegerField()
    steals = models.IntegerField()
    blocks = models.IntegerField()
    turnovers = models.IntegerField()

    free_throws_made = models.IntegerField()
    free_throws_attempted = models.IntegerField()
    twos_made = models.IntegerField()
    twos_attempted = models.IntegerField()
    threes_made = models.IntegerField()
    threes_attempted = models.IntegerField()
    field_goals_made = models.IntegerField()
    field_goals_attempted = models.IntegerField()

    def __str__(self):
        return '{} - {}'.format(self.player, self.game)

    @property
    def rebounds(self):
        return self.defensive_rebounds + self.offensive_rebounds

    @property
    def twos(self):
        return self.twos_made

    @property
    def threes(self):
        return self.threes_made

    @property
    def free_throws(self):
        return self.free_throws_made

    @property
    def points(self):
        return int(self.twos) * 2 + int(self.threes) * 3 + int(self.free_throws)

    @property
    def efficiency_rating(self):
        """
        The NBA's Efficiency Rating is a single number measure of a player's overall contribution (both positive and
        negative) to a game he plays in.((Points + Rebounds + Assists + Steals + Blocks) - ((Field Goals Att. - Field
        Goals Made) + (Free Throws Att. -Free Throws Made) + Turnovers))
        """

        calculation_base = self.points + self.rebounds + self.assists + self.steals + self.blocks
        points = self.field_goals_attempted - self.field_goals_made
        free_throws = self.free_throws_attempted - self.free_throws_made

        return calculation_base - points + free_throws + self.turnovers

    @property
    def assist_to_turnover_ratio(self):
        """
        The number of assists for player or team compared to the number of turnovers they have committed
        """
        return float(self.assists) / float(self.turnovers)

    @property
    def steal_to_turnover_ratio(self):
        """
        The number of steals a player of team has compared to the number of turnovers they have committed
        """
        return float(self.turnovers) / float(self.steals)

    @property
    def points_per_min(self):
        return round(self.draft_king_points / float(self.minutes), 2) if self.minutes > 0 else 0

    @property
    def draft_king_points(self):
        """
        Draft King Scoring can be found at https://www.draftkings.com/help/nba
        """
        points = 0.0
        stats_over_10 = 0

        for k, v in settings.DRAFT_KING_POINTS.items():
            if hasattr(self, k):
                category_points = int(getattr(self, k)) * v
                points += category_points
                if category_points / v >= 10 and k in ('rebounds', 'steals', 'assists', 'blocks'):
                    stats_over_10 += 1

        if int(self.twos_made) * 2 + int(self.threes_made) * 3 + int(self.free_throws_made) >= 10:
            stats_over_10 += 1

        if stats_over_10 >= 3:
            points += settings.DRAFT_KING_POINTS['triple_double']
        if stats_over_10 == 2:
            points += settings.DRAFT_KING_POINTS['double_double']

        return points


class Contest(models.Model):
    name = models.CharField(max_length=64)
    entree_fee = models.DecimalField(max_digits=16, decimal_places=2)
    entries = models.IntegerField()
    total_entries = models.IntegerField()


class ContestPayout(models.Model):
    contest = models.ForeignKey('Contest')
    start = models.IntegerField()
    stop = models.IntegerField()  # inclusive
    value = models.DecimalField(max_digits=16, decimal_places=2)
