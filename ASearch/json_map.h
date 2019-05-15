#ifndef JSON_MAP_H
#define JSON_MAP_H

#include <iostream>
#include "gl_const.h"
#include <sstream>
#include <string>
#include <algorithm>
#include <vector>
#include "json.hpp"
#include <fstream>

using namespace nlohmann;

struct obstacle
{
    int lu_i;
    int lu_j;
    int rb_i;
    int rb_j;
};

class JSON_Map
{
public:
    JSON_Map();
    bool getMap(const char *FileName);
    bool CellIsTraversable (int i, int j) const;
    bool CellOnGrid (int i, int j) const;
    bool CellIsObstacle(int i, int j) const;
    int  getValue(int i, int j) const;
    void createGrid();
    bool lineOfSight(int i1, int j1, int i2, int j2) const;


    int     height, width;
    int     start_i, start_j;
    int     goal_i, goal_j;
    int     cur_goal_i, cur_goal_j;
    int     cellsize;
    std::vector<obstacle> obstacles;
    std::vector<std::vector<int>> grid;
};

#endif // JSON_MAP_H
