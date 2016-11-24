
class Probability(object):

    @classmethod
    def of_target(cls, player, start, stop=None, game_logs=None):

        if game_logs is None:
            game_logs = player.gamelog_set.all()

        total_games = game_logs.count()

        if total_games == 0:
            return 0

        total_hits = 0
        for gl in game_logs:
            if stop is None and gl.draft_king_points >= start:
                total_hits += 1
            elif start <= gl.draft_king_points < stop:
                total_hits += 1

        return total_hits / float(total_games)
