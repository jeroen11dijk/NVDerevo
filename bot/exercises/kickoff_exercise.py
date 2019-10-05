from dataclasses import dataclass, field
from math import pi
from pathlib import Path
from typing import List, Optional

from rlbot.matchcomms.common_uses.reply import send_and_wait_for_replies
from rlbot.matchcomms.common_uses.set_attributes_message import make_set_attributes_message
from rlbot.matchconfig.match_config import PlayerConfig, Team
from rlbot.training.training import Grade
from rlbot.utils.game_state_util import BallState, CarState, GameState, Physics, Rotator, Vector3
from rlbot.utils.game_state_util import BoostState
from rlbottraining.grading.grader import Grader
from rlbottraining.rng import SeededRandomNumberGenerator
from rlbottraining.training_exercise import TrainingExercise, Playlist

from kickoff_grader import KickoffGrader


@dataclass
class SpawnLocation:
    pos: Vector3
    rot: Rotator


class Spawns():
    """Default Kickoffs Spawns (BLUE)"""
    CORNER_R = SpawnLocation(Vector3(-2048, -2560, 18), Rotator(0, 0.25 * pi, 0))
    CORNER_L = SpawnLocation(Vector3(2048, -2560, 18), Rotator(0, 0.75 * pi, 0))
    BACK_R = SpawnLocation(Vector3(-256, -3840, 18), Rotator(0, 0.5 * pi, 0))
    BACK_L = SpawnLocation(Vector3(256.0, -3840, 18), Rotator(0, 0.5 * pi, 0))
    STRAIGHT = SpawnLocation(Vector3(0, -4608, 18), Rotator(0, 0.5 * pi, 0))


@dataclass
class KickoffExercise(TrainingExercise):
    grader: Grader = field(default_factory=KickoffGrader)
    blue_spawns: List[SpawnLocation] = field(default_factory=list)
    orange_spawns: List[SpawnLocation] = field(default_factory=list)

    def __post_init__(self):
        """Flip the orange spawns around to get the correct location and combine the two spawns."""
        orange_spawns = [
            SpawnLocation(Vector3(-spawn.pos.x, -spawn.pos.y, spawn.pos.z),
                          Rotator(spawn.rot.pitch, spawn.rot.yaw + pi, spawn.rot.roll))
            for spawn in self.orange_spawns]
        self.spawns = self.blue_spawns + orange_spawns

    def on_briefing(self) -> Optional[Grade]:
        _ = send_and_wait_for_replies(self.get_matchcomms(), [
            make_set_attributes_message(1, {'kickoff': True, 'prev_kickoff': False}),
        ])

    def make_game_state(self, rng: SeededRandomNumberGenerator) -> GameState:
        num_players = self.match_config.num_players
        assert num_players == len(self.spawns), 'Number of players does not match the number of spawns.'

        car_states = {}
        for index in range(num_players):
            car_states[index] = CarState(
                boost_amount=33,
                physics=Physics(
                    location=self.spawns[index].pos,
                    velocity=Vector3(0, 0, 0),
                    rotation=self.spawns[index].rot,
                    angular_velocity=Vector3(0, 0, 0)
                )
            )

        ball_state = BallState(
            Physics(
                location=Vector3(0, 0, 93),
                velocity=Vector3(0, 0, 0),
                rotation=Rotator(0, 0, 0),
                angular_velocity=Vector3(0, 0, 0)
            )
        )

        # game_state = GameState(ball=ball_state, cars=car_states, console_commands=['Set WorldInfo TimeDilation 0.5'])
        game_state = GameState(ball=ball_state, cars=car_states, console_commands=['Set WorldInfo TimeDilation 1'], boosts={i: BoostState(0) for i in range(34)})
        return game_state


def make_default_playlist() -> Playlist:
    # Choose which spawns you want to test.
    exercises = [
        KickoffExercise('Right Corner', blue_spawns=[Spawns.CORNER_R], orange_spawns=[Spawns.CORNER_R]),
        KickoffExercise('Left Corner', blue_spawns=[Spawns.CORNER_L], orange_spawns=[Spawns.CORNER_L]),
        KickoffExercise('Back Right', blue_spawns=[Spawns.BACK_R], orange_spawns=[Spawns.BACK_R]),
        KickoffExercise('Back Left', blue_spawns=[Spawns.BACK_L], orange_spawns=[Spawns.BACK_L]),
        KickoffExercise('Straight', blue_spawns=[Spawns.STRAIGHT], orange_spawns=[Spawns.STRAIGHT]),
    ]

    for ex in exercises:
        # The length of players in the match_config needs to match the number or spawns.

        # Replace with path to your bot or bots.
        ex.match_config.player_configs = \
            [PlayerConfig.bot_config(Path(Path(__file__).absolute().parent.parent.parent / 'Derevo.cfg'), Team.BLUE) for
             _ in ex.blue_spawns] + \
            [PlayerConfig.bot_config(Path(Path(__file__).absolute().parent.parent.parent / 'Derevo.cfg'), Team.ORANGE)
             for _ in ex.orange_spawns]

    return exercises
