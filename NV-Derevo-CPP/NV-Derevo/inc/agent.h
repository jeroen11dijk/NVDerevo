#pragma once
#include "rlbot/bot.h"
#include "simulation/game.h"
#include "simulation/car.h"
#include "rlbot/renderer.h"
#include "mechanics/dodge.h"
#include "mechanics/drive.h"
#include <memory>

enum Step {Driving, Steering, Driving_1, Dodging, Dodging_1, Dodging_2};

class NVDerevo : public Bot
{
    Drive* drive = nullptr;
    Dodge* dodge = nullptr;
    Renderer renderer;

    vec3 our_goal;
    vec3 their_goal;

    bool kickoff = false;
    bool prev_kickoff = false;
    bool kickoff_start = false;
    bool closest_to_ball = false;
    bool has_to_go = false;
    std::vector<Car*> teammates;
    std::vector<Ball> ball_prediction;

    Step step = Driving;
    

public:
    NVDerevo(int index, int team, std::string name, Game & game);

    void initialize_agent();

    Input GetOutput(Game game);
    bool ClosestToBall(Game game);
    vec3 GetIntersect(Game game, Car car);
};