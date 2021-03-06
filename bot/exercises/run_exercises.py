from pathlib import Path

from rlbot.matchconfig.match_config import PlayerConfig, Team
from rlbottraining.common_exercises.bronze_striker import *
from rlbottraining.common_exercises.silver_goalie import *
from rlbottraining.common_exercises.silver_striker import HookShot


def make_default_playlist() -> Playlist:
    # Choose which spawns you want to test.
    exercises = [
        RollingTowardsGoalShot('Rolling Shot'),
        HookShot('Hookshot'),
        FacingAwayFromBallInFrontOfGoal('Facing away from opponents goal', car_start_x=200., car_start_y=5100),
    ]

    for ex in exercises:
        # The length of players in the match_config needs to match the number or spawns.

        # Replace with path to your bot or bots.
        ex.match_config.player_configs = [
            PlayerConfig.bot_config(Path(__file__).absolute().parent.parent.parent / 'Derevo.cfg', Team.BLUE)]

    return exercises
