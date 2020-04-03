#include "rlbot/bot.h"
#include "simulation/game.h"
#include "simulation/car.h"
#include "simulation/field.h"
#include "rlbot/renderer.h"
#include "agent.h"
#include "kickoff.h"
#include "utils.h"
#include <memory>
#include <time.h>

NVDerevo::NVDerevo(int index, int team, std::string name, Game &game)
    : Bot(index, team, name), renderer(index)
{
    Field::initialize_soccar();
    if (team == 1) {
        our_goal = vec3{0, 5120, 321};
        their_goal = vec3{0, -5120, 321};
    } else {
        our_goal = vec3{0, -5120, 321};
        their_goal = vec3{0, 5120, 321};
    }
    drive = new Drive(*game.my_car);
    dodge = new Dodge(*game.my_car);
    turn = new Reorient(*game.my_car);
}

Input NVDerevo::GetOutput(Game game)
{
    prev_kickoff = kickoff;
    kickoff = game.kickoff_pause;
    teammates.clear();
    for (int i = 0; i < game.num_cars; i++)
    {
        if (game.cars[i].team == team && i != index)
        {
            teammates.push_back(&game.cars[i]);
        }
    }
    Ball ball = Ball(game.ball);
    ball_prediction.clear();
    for (int i = 0; i < 360; i++)
    {
        ball.step(1 / 60);
        ball_prediction.push_back(ball);
    }
    closest_to_ball = ClosestToBall(game);
    // Kick off stuff
    if (kickoff and not prev_kickoff)
    {
        if (teammates.size() > 0)
        {
            if (closest_to_ball)
            {
                InitKickoff(*this, game);
                has_to_go = true;
            }
            else
            {
                drive->target = our_goal;
                drive->speed = 1410;
            }
        }
        else
        {
            InitKickoff(*this, game);
            has_to_go = true;
        }
    }
    if ((kickoff or step == Dodging_2) and has_to_go) {
        KickOff(*this, game);
    } else if (kickoff and not has_to_go) {
        drive->target = our_goal;
        drive->speed = 1410;
    } else {
        if (has_to_go) {
            has_to_go = false;
        }
        //TODO
        //get_controls()
        // Pass this along with *this
        GetControls(game);
    }
    if (not game.round_active) {
        controls.steer = 0;
    }
    return controls;
}

void NVDerevo::GetControls(Game & game) {
    if (closest_to_ball) {
        drive->target = game.ball.position;
        drive->speed = 1410;
    } else {
        drive->target = our_goal;
        drive->speed = 1410;
    }
    drive->step(game.time_delta);
    controls = drive->controls;
}

bool NVDerevo::ClosestToBall(Game & game)
{
    float dist_to_ball = std::numeric_limits<float>::max();
    for (size_t i = 0; i < teammates.size(); i++)
    {
        Car teammate_car = *teammates[i];
        if (Distance2D(teammate_car.position, GetIntersect(game, teammate_car)) < dist_to_ball)
        {
            dist_to_ball = Distance2D(teammate_car.position, GetIntersect(game, teammate_car));
        }
    }
    return Distance2D(game.my_car->position, GetIntersect(game, *game.my_car)) < dist_to_ball;
}

vec3 NVDerevo::GetIntersect(Game & game, Car car)
{
    float intercept_time = (norm(game.ball.position - car.position) - 200) / std::max(1.0f, norm(car.velocity));
    int intercept_index = Cap(static_cast<int>(intercept_time * 60), 0, ball_prediction.size());
    return ball_prediction[intercept_index].position;
}