#pragma once
#include "linear_algebra/math.h"
#include "agent.h"

inline float Distance2D(vec3 a, vec3 b) {
    return norm(vec2(a - b));
}

inline int Cap(int num, int low, int high) {
    return std::min(std::max(num, low), high);
}

int sign(int num);

void GetControls(NVDerevo & derevo, Game & game);