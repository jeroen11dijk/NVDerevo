#include "utils.h"

void GetControls(NVDerevo & derevo, Game & game) {
    if (derevo.closest_to_ball) {
        derevo.drive->target = game.ball.position;
        derevo.drive->speed = 1410;
    } else {
        derevo.drive->target = derevo.our_goal;
        derevo.drive->speed = 1410;
    }
    derevo.drive->step(game.time_delta);
    derevo.controls = derevo.drive->controls;
}

int sign(int num) {
    if (num <= 0) return -1;
    return 1;
}