from django import template


register = template.Library()


@register.simple_tag
def string(obj):
    if obj:
        return str(obj)


@register.simple_tag
def game_count_for_season(player, season):
    if player:
        if season:
            return player.game_logs_for_season(season).count()
        return player.games.count()


@register.simple_tag
def avg_mins_for_season(player, season):
    if player:
        if season:
            return player.average_minutes(game_logs=player.game_logs_for_season(season))
        return player.average_minutes()


@register.simple_tag
def avg_pts_for_season(player, season):
    if player:
        if season:
            return player.average_points(game_logs=player.game_logs_for_season(season))
        return player.average_points()


@register.simple_tag
def avg_ppm_for_season(player, season):
    if player:
        if season:
            return player.average_ppm(game_logs=player.game_logs_for_season(season))
        return player.average_ppm()


@register.simple_tag
def avg_mins_last_x_games(player, x):
    if player:
        return player.average_minutes(game_logs=player.game_logs_last_x_days(x))


@register.simple_tag
def avg_pts_last_x_games(player, x):
    if player:
        return player.average_points(game_logs=player.game_logs_last_x_days(x))


@register.simple_tag
def avg_ppm_last_x_games(player, x):
    if player:
        game_logs = player.game_logs_last_x_days(x)
        return player.average_points(game_logs=game_logs) / player.average_minutes(game_logs=game_logs)



@register.simple_tag
def game_count_for_season(player, season):
    if player:
        if season:
            return player.game_logs_for_season(season).count()
        return player.games.count()
