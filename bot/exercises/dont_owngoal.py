from pathlib import Path

from rlbot.matchconfig.match_config import PlayerConfig, Team
from rlbottraining.common_exercises.silver_goalie import *


def make_default_playlist() -> Playlist:
    # Choose which spawns you want to test.
    exercises = [
        DefendBallRollingTowardsGoal('DefendBallRollingTowardsGoal'),
        LineSave('LineSave'),
        TryNotToOwnGoal('TryNotToOwnGoal'),
    ]

    for ex in exercises:
        # The length of players in the match_config needs to match the number or spawns.

        # Replace with path to your bot or bots.
        ex.match_config.player_configs = [PlayerConfig.bot_config(Path(__file__).absolute().parent.parent.parent / 'Derevo.cfg', Team.BLUE)]

    return exercises
