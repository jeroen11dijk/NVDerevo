#pragma once
#include "rlbot/bot.h"
#include "simulation/game.h"
#include "simulation/car.h"
#include "rlbot/renderer.h"
#include "mechanics/reorient.h"
#include "mechanics/dodge.h"
#include "mechanics/drive.h"
#include <memory>

enum Step {Shooting, Driving, Steering, Driving_1, Dodging, Dodging_1, Dodging_2};
enum KickOffStart {Center, OffCenter, Diagonal};

class NVDerevo : public Bot
{
    public:
    Input controls = Input();

    Drive* drive = nullptr;
    Dodge* dodge = nullptr;
    Reorient* turn = nullptr; 
    Renderer renderer;

    vec3 our_goal;
    vec3 their_goal;

    bool kickoff = false;
    bool prev_kickoff = false;
    KickOffStart kickoff_start = Center;
    bool closest_to_ball = false;
    bool has_to_go = false;
    std::vector<Car*> teammates;
    std::vector<Ball> ball_prediction;

    Step step = Driving;
    
    NVDerevo(int index, int team, std::string name, Game & game);

    void initialize_agent();

    Input GetOutput(Game game);
    bool ClosestToBall(Game game);
    vec3 GetIntersect(Game game, Car car);
};