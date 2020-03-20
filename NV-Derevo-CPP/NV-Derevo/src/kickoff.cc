#include "kickoff.h"
#include "utils.h"


void InitKickoff(NVDerevo & derevo, Game & game) {
    vec3 target;
    if (abs(game.my_car->position[0]) < 250) {
        target = vec3{sign(derevo.team) * 20.0f, sign(derevo.team) * 4240.0f, 6.0f};
        derevo.kickoff_start = Center;
    } else if (abs(game.my_car->position[0]) < 1000) {
        target = vec3{0.0f, sign(derevo.team) * (2816.0f + 300.0f), 70.0f};
        derevo.kickoff_start = OffCenter;
    } else {
        target = game.my_car->position + 300 * game.my_car->forward();
        derevo.kickoff_start = Diagonal;
    }
    derevo.drive = new Drive(*game.my_car);
    derevo.drive->target = target;
    derevo.drive->speed = 2400;
    derevo.step = Driving;
    derevo.drive->step(game.time_delta);
    derevo.controls = derevo.drive->controls;    
}

void KickOff(NVDerevo & derevo, Game & game) {
    Ball ball = game.ball;
    Car car = *game.my_car;
    float t = Distance2D(ball.position, car.position) / 2200;
    float batmobile_resting = 18.65f;
    vec3 robbies_constant = (ball.position - vec3{0, 0, 92.75f - batmobile_resting} - car.position - car.velocity * t) * 2 * std::pow(t, -2);
    bool robbies_boost_constant = dot(normalize(xy(car.forward())), normalize(xy(robbies_constant))) > (car.on_ground ? 0.3 : 0.1);
    // Module that performs the kickoffs
    std::cout << derevo.step << std::endl;
    if (derevo.kickoff_start == Diagonal) {
        if (derevo.step == Driving) {
            derevo.drive->step(game.time_delta);
            derevo.controls = derevo.drive->controls;
            if (derevo.drive->finished) {
                vec3 ball_location = ball.position + vec3{0, -sign(derevo.team) * 500.0f, 0};
                vec3 target = car.position + 250 * normalize(ball_location - car.position);
                derevo.drive = new Drive(*game.my_car);
                derevo.drive->target = target;
                derevo.drive->speed = 2400;
                derevo.step = Driving_1;
            }
        } else if (derevo.step == Driving_1) {
            derevo.drive->step(game.time_delta);
            derevo.controls = derevo.drive->controls;
            if (derevo.drive->finished) {
                float target_degrees = -sign(derevo.team) * sign(car.position[0]) * 60.0f;
                float target_radians = (atan(1.0f)* 4.0f * target_degrees) / 180.0f;
                vec3 target = vec3(dot(rotation(target_radians), vec2(car.forward())) * 10000.0f);
                float rot_degrees = -sign(derevo.team) * -sign(car.position[0]) * 30.0f;
                float rot_radians = (atan(1.0f)* 4.0f * rot_degrees) / 180.0f;
                mat3 preorientation = dot(axis_to_rotation(vec3{0, 0, rot_radians}), car.orientation);
                SetupFirstDodge(derevo, game, 0.05, 0.3, target, preorientation);
            }
        } else if (derevo.step == Dodging_1) {
            if (derevo.dodge->timer > 0.8) {
                vec3 lerp_var = lerp(normalize(robbies_constant), normalize(ball.position - vec3{0.0f, 0.0f, 92.75f - batmobile_resting} - car.position), 0.8f);
                derevo.turn->target_orientation = look_at(lerp_var, vec3{0, 0, 1});
                derevo.turn->step(game.time_delta);
                derevo.controls = derevo.turn->controls;
                if (car.on_ground) {
                    derevo.step = Shooting;
                }
            } else {
                derevo.dodge->step(game.time_delta);
                derevo.controls = derevo.dodge->controls;
            }
            derevo.controls.boost = robbies_boost_constant;
        }
    } else if (derevo.kickoff_start == Center) {
        if (derevo.step == Driving) {
            derevo.drive->step(game.time_delta);
            derevo.controls = derevo.drive->controls;
            if (derevo.drive->finished) {
                float target_degrees = -65.0f;
                float target_radians = (atan(1.0f)* 4.0f * target_degrees) / 180.0f;
                vec3 target = vec3(dot(rotation(target_radians), vec2{car.forward()}) * 10000.0f);
                float rot_degrees = 45.0f;
                float rot_radians = (atan(1.0f)* 4.0f * rot_degrees) / 180.0f;
                mat3 preorientation = dot(axis_to_rotation(vec3{0, 0, rot_radians}), car.orientation);
                SetupFirstDodge(derevo, game, 0.05, 0.4, target, preorientation);
            }
        } else if (derevo.step == Dodging_1) {
            if (derevo.dodge->timer > 0.8) {
                derevo.turn->target_orientation = look_at(xy(ball.position - car.position), vec3{0, 0, 1});
                derevo.turn->step(game.time_delta);
                derevo.controls = derevo.turn->controls;
                SetSteer(derevo, game);
            } else {
                derevo.dodge->step(game.time_delta);
                derevo.controls = derevo.dodge->controls;
            }
            derevo.controls.boost = robbies_boost_constant;
        } else if (derevo.step == Steering) {
            derevo.drive->step(game.time_delta);
            derevo.controls = derevo.drive->controls;
            if (Distance2D(car.position, ball.position) < 800) {
                derevo.dodge = new Dodge(*game.my_car);
                derevo.dodge->duration = 0.075;
                derevo.dodge->target = ball.position;
                derevo.step = Dodging_2;
            }
        } else if (derevo.step == Dodging_2) {
            derevo.dodge->step(game.time_delta);
            derevo.controls = derevo.dodge->controls;
            if (derevo.dodge->finished && car.on_ground) {
                derevo.step = Shooting;
            }
        }
    } else if (derevo.kickoff_start == OffCenter) {
        if (derevo.step == Driving) {
            derevo.drive->step(game.time_delta);
            derevo.controls = derevo.drive->controls;
            if (Distance2D(car.position, derevo.drive->target) < 650) {
                float target_degrees = -sign(derevo.team) * -sign(car.position[0]) * 100.0f;
                float target_radians = (atan(1.0f)* 4.0f * target_degrees) / 180.0f;
                vec3 target = vec3(dot(rotation(target_radians), vec2(car.forward())) * 10000.0f);
                float rot_degrees = -sign(derevo.team) * sign(car.position[0]) * 30.0f;
                float rot_radians = (atan(1.0f)* 4.0f * rot_degrees) / 180.0f;
                mat3 preorientation = dot(axis_to_rotation(vec3{0, 0, rot_radians}), car.orientation);
                std::cout << "CPP: " << game.my_car->position << std::endl;
                std::cout << "CPP: " << (atan(1.0f)* 4.0f * target_degrees) / 180.0f << std::endl;
                SetupFirstDodge(derevo, game, 0.05, 0.4, target, preorientation);
            }
        }  else if (derevo.step == Dodging_1) {
            if (derevo.dodge->timer > 0.8) {
                vec3 lerp_var = lerp(normalize(robbies_constant), normalize(ball.position - vec3{0.0f, 0.0f, 92.75f - batmobile_resting} - car.position), 0.25f);
                derevo.turn->target_orientation = look_at(lerp_var, vec3{0, 0, 1});
                derevo.turn->step(game.time_delta);
                derevo.controls = derevo.turn->controls;
                SetSteer(derevo, game);
            } else {
                derevo.dodge->step(game.time_delta);
                derevo.controls = derevo.dodge->controls;
            }
            derevo.controls.boost = robbies_boost_constant;
        } else if (derevo.step == Steering) {
            derevo.drive->step(game.time_delta);
            derevo.controls = derevo.drive->controls;
            if (Distance2D(ball.position, car.position) < 800) {
                derevo.dodge = new Dodge(*game.my_car);
                derevo.dodge->duration = 0.075;
                derevo.dodge->target = ball.position;
                derevo.step = Dodging_2;
            }
        } else if (derevo.step == Dodging_2) {
            derevo.dodge->step(game.time_delta);
            derevo.controls = derevo.dodge->controls;
            if (derevo.dodge->finished && car.on_ground) {
                derevo.step = Shooting;
            }
        }
    }
}

void SetSteer(NVDerevo & derevo, Game & game) {
    if (game.my_car->on_ground) {
        derevo.step = Steering;
        derevo.drive = new Drive(*game.my_car);
        derevo.drive->target = game.ball.position;
        derevo.drive->speed = 2400;
    }
}

void SetupFirstDodge(NVDerevo & derevo, Game & game, float duration, float delay, vec3 target, mat3 preorientation) {
    derevo.dodge = new Dodge(*game.my_car);
    derevo.turn = new Reorient(*game.my_car);
    derevo.dodge->duration = duration;
    derevo.dodge->delay = delay;
    derevo.dodge->target = target;
    derevo.dodge->preorientation = preorientation;
    derevo.step = Dodging_1;
}