from pathlib import Path

from rlbot.matchconfig.match_config import PlayerConfig, Team
from rlbottraining.common_exercises.silver_goalie import *


class LineSave2(GoalieExercise):
    """A test where the ball is put on the line and the player in the middle of the field"""

    def make_game_state(self, rng: SeededRandomNumberGenerator) -> GameState:
        car_pos = Vector3(0, 2500, 18)
        ball_pos = Vector3(0, -5000, 100)
        ball_state = BallState(Physics(location=ball_pos, velocity=Vector3(0, 0, 0), angular_velocity=Vector3(0, 0, 0)))
        car_state = CarState(boost_amount=87, physics=Physics(location=car_pos, velocity=Vector3(0, 0, 0),
                                                              angular_velocity=Vector3(0, 0, 0),
                                                              rotation=Rotator(0, -pi / 2, 0)))
        enemy_car = CarState(physics=Physics(location=Vector3(10000, 10000, 10000)))
        game_state = GameState(ball=ball_state, cars={0: car_state, 1: enemy_car})
        return game_state


def make_default_playlist() -> Playlist:
    # Choose which spawns you want to test.
    exercises = [
        DefendBallRollingTowardsGoal('DefendBallRollingTowardsGoal'),
        LineSave2('LineSave'),
        TryNotToOwnGoal('TryNotToOwnGoal'),
    ]

    for ex in exercises:
        # The length of players in the match_config needs to match the number or spawns.

        # Replace with path to your bot or bots.
        ex.match_config.player_configs = [
            PlayerConfig.bot_config(Path(__file__).absolute().parent.parent.parent / 'Derevo.cfg', Team.BLUE)]

    return exercises
