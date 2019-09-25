"""Module to keep track of all the boost pads."""
from rlutilities.linear_algebra import vec3


class BoostPad:
    """Class to keep track of all the boost pads."""

    def __init__(self, index, location, is_active, timer):
        self.index = index
        self.location = location
        self.is_active = is_active
        self.timer = timer


def init_boostpads(agent):
    """Method to initialize the boost pads."""
    agent.boost_pads = []
    agent.small_boost_pads = []
    field_info = agent.get_field_info()
    for i in range(field_info.num_boosts):
        current = field_info.boost_pads[i]
        if field_info.boost_pads[i].is_full_boost:
            agent.boost_pads.append(
                BoostPad(i, vec3(current.location.x, current.location.y, current.location.z), True, 0.0))
        else:
            agent.small_boost_pads.append(
                BoostPad(i, vec3(current.location.x, current.location.y, current.location.z), True, 0.0))


def update_boostpads(agent, packet):
    """Method to update the boost pads."""
    for i in range(0, len(agent.boost_pads)):
        boost_pad = packet.game_boosts[agent.boost_pads[i].index]
        agent.boost_pads[i].is_active = boost_pad.is_active
        agent.boost_pads[i].timer = boost_pad.timer

    for i in range(0, len(agent.small_boost_pads)):
        boost_pad = packet.game_boosts[agent.small_boost_pads[i].index]
        agent.small_boost_pads[i].is_active = boost_pad.is_active
        agent.small_boost_pads[i].timer = boost_pad.timer
