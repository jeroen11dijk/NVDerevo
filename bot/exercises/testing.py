import unittest

from rlbot.training.training import Pass
from rlbottraining.exercise_runner import run_playlist

from dont_owngoal import make_default_playlist


class MainTest(unittest.TestCase):

    def test_defend_ball_rolling_towards_goal(self):
        result_iter = run_playlist(make_default_playlist())
        results = list(result_iter)
        self.assertEqual(len(results), 3)
        for result in results:
            self.assertIsInstance(result.grade, Pass)


if __name__ == '__main__':
    unittest.main()
