from datetime import datetime

from django.db.models import Avg

from basketball.models import Game, Season, Team


class NBAManager(object):
    """
    Class to provide methods for managing ELO rankings in the NBA
    """

    K = 20

    @classmethod
    def apply_all_data(cls):
        seasons = Season.objects.all().order_by('name')

        for season in seasons:
            all_teams = Team.objects.all()

            average_elo = all_teams.aggregate(Avg('elo'))['elo__avg']

            for team in all_teams:
                team.elo = ELO.season_carry_over(team.elo, average_elo)
                team.save()

            cls.apply_season(season)

    @classmethod
    def apply_season(cls, season):
        games = Game.objects.filter(season=season, date__lt=datetime.now().date()).order_by('date')
        cls.apply_games(games)

    @classmethod
    def apply_games(cls, games):
        """Updates each Team's ELO ranking based on their performance in the games provided.

        Args:
            games: Iterable of games, sorted by ascending date

        Returns:
            None
        """
        for game in games:

            # margin of victory
            mov = abs(game.home_team_score() - game.away_team_score())

            # assign the ELOs going into the game
            game.home_elo = game.home_team.elo
            game.away_elo = game.away_team.elo

            # figure out who won and adjust ELO
            if game.home_team is game.winner():
                elo_change = ELO.elo_change(cls.K, game.home_elo + 100, game.away_elo, mov)
                game.home_team.elo += elo_change
                game.away_team.elo -= elo_change
            else:
                elo_change = ELO.elo_change(cls.K, game.away_elo, game.home_elo + 100, mov)
                game.home_team.elo -= elo_change
                game.away_team.elo += elo_change

            # Save changes
            game.save()
            game.home_team.save()
            game.away_team.save()


class ELO(object):

    @classmethod
    def point_spread(cls, elo_diff):
        """Returns the estimated point spread based on the difference in their ELOs

        Args:
            elo_diff: The difference between the 2 team's ELOs

        Returns:
            The point spread
        """
        return (abs(elo_diff) + 100.0) / 28.0

    @classmethod
    def umov(cls, mov, elo_diff):
        """Calculates the **margin of victory multiplier**

        Args:
            mov: The margin of victory
            elo_diff: The difference between the two teams ELOs (negative if underdog won)

        Returns:
            The margin of victory multiplier
        """
        return pow(mov + 3.0, 0.8) / (7.5 + (0.006 * elo_diff))

    @classmethod
    def win_probability(cls, elo_diff):
        """Calculates the win probably given the difference between 2 ELOs
        Args:
            elo_diff: The difference between 2 teams ELOs

        Returns:
            The win probability
        """
        elo_diff *= -1.0
        return 1.0 / float(1.0 + pow(10.0, elo_diff / 400.0))

    @classmethod
    def elo_change(cls, k, winner_elo, loser_elo, mov):
        """Calculates the change in ELO score based on some provided information.

        Args:
            k: auto correlation multiplier
            winner_elo: Winner's current ELO
            loser_elo: Loser's current ELO
            mov: The margin of victory

        Returns:
            The change in ELO
        """
        elo_diff = winner_elo - loser_elo
        actual_result = 1
        expected_result = cls.win_probability(elo_diff)
        return k * cls.umov(mov, elo_diff) * (actual_result - expected_result)

    @classmethod
    def season_carry_over(cls, eos_elo, avg_elo):
        """Calculates the ELO for a team as it transitions from last season into next.

        Args:
            eos_elo: End of season ELO
            avg_elo: Average ELO of all the teams

        Returns:
            The ELO going into the new season.
        """
        return (0.75 * eos_elo) + (0.25 * avg_elo)
