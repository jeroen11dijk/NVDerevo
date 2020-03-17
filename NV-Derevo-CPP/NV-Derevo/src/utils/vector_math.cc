#include "utils/vector_math.h"

vec3 nearest_point(const vec3 & pos, const std::vector<vec3> & points)
{
    float best_dist = std::numeric_limits<float>::max();
    vec3 best_point;

    for (const vec3 & point : points)
    {
        float dist = distance(pos, point);
        if (dist < best_dist)
        {
            best_dist = dist;
            best_point = point;
        }
    }
    return best_point;
}

vec3 furthest_point(const vec3 & pos, const std::vector<vec3> & points)
{
    float best_dist = std::numeric_limits<float>::min();
    vec3 best_point;
    
    for (const vec3 & point : points)
    {
        float dist = distance(pos, point);
        if (dist > best_dist)
        {
            best_dist = dist;
            best_point = point;
        }
    }
    return best_point;
}