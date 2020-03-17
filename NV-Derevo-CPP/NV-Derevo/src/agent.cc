#include "rlbot/bot.h"
#include "mechanics/drive.h"
#include "simulation/game.h"
#include "simulation/car.h"
#include "simulation/field.h"
#include "rlbot/renderer.h"
#include "agent.h"
#include <memory>
#include <time.h>

Spikeroog::Spikeroog(int index, int team, std::string name, Game & game)
: Bot(index, team, name), renderer(index)
{
    Field::initialize_soccar();
    drive = new Drive(*game.my_car);
}

Input Spikeroog::GetOutput(Game game)
{
    // finally, return the controls
    drive->target = game.ball.position;
    drive->speed = 1410;
    drive->step(1/60);
    return drive->controls;
}