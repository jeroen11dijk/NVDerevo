import unittest
from pathlib import Path

from rlbot.matchconfig.match_config import PlayerConfig, Team
from rlbot.training.training import Pass
from rlbottraining.exercise_runner import run_playlist
from rlbottraining.common_exercises.silver_striker import HookShot

from dont_owngoal import make_default_playlist


class MainTest(unittest.TestCase):

    def test_defend_ball_rolling_towards_goal(self):
        result_iter = run_playlist(make_default_playlist())
        results = list(result_iter)
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result.grade, Pass)

    def test_hookshot(self):
        exercise = HookShot('Hookshot')
        exercise.match_config.player_configs = [
            PlayerConfig.bot_config(Path(__file__).absolute().parent.parent.parent / 'Derevo.cfg', Team.BLUE)
        ]
        result_iter = run_playlist([exercise])
        results = list(result_iter)
        result = results[0]
        self.assertEqual(len(results), 1)
        self.assertEqual(result.exercise.name, 'Hookshot')
        self.assertIsInstance(result.grade, Pass)


if __name__ == '__main__':
    unittest.main()
