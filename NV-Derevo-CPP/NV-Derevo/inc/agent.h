#pragma once
#include "rlbot/bot.h"
#include "simulation/game.h"
#include "simulation/car.h"
#include "rlbot/renderer.h"
#include "../../RLUtilities/inc/simulation/game.h"
#include "../../RLUtilities/inc/mechanics/drive.h"
#include <memory>


class Spikeroog : public Bot
{

    Drive* drive = nullptr;
    Renderer renderer;

public:
    Spikeroog(int index, int team, std::string name, Game & game);

    Input GetOutput(Game game);
};