#include "json_map.h"

JSON_Map::JSON_Map()
{

}

bool JSON_Map::getMap(const char *FileName)
{
    std::ifstream ifs(FileName);
    json j = json::parse(ifs);
    cellsize = j["current-action"]["cell-size"][0];
    std::cout<<"a";
    height = j["map"]["map_size"][0];
    std::cout<<"b";
    height/=cellsize;
    width = j["map"]["map_size"][1];
    std::cout<<"c";
    width/=cellsize;
    obstacle obs;
    for(int i = 4; i < j["map"]["wall"].size(); i++)
    {
        obs.lu_j = j["map"]["wall"][i][0];
        obs.lu_j/=cellsize;
        obs.lu_i = j["map"]["wall"][i][1];
        obs.lu_i/=cellsize;
        obs.rb_j = j["map"]["wall"][i][2];
        obs.rb_j/=cellsize;
        obs.rb_i = j["map"]["wall"][i][3];
        obs.rb_i/=cellsize;
        std::cout<<"d";
        obstacles.push_back(obs);
    }
    if(j["map"].find("vanished") != j["map"].end())
    {
        //for(int i = 0; i < j["map"]["vanished"]["wall"].size(); i++)
        {
            obs.lu_j = j["map"]["vanished"]["wall"][0];
            obs.lu_j/=cellsize;
            obs.lu_i = j["map"]["vanished"]["wall"][1];
            obs.lu_i/=cellsize;
            obs.rb_j = j["map"]["vanished"]["wall"][2];
            obs.rb_j/=cellsize;
            obs.rb_i = j["map"]["vanished"]["wall"][3];
            std::cout<<"e";
            obs.rb_i/=cellsize;
            obstacles.push_back(obs);
        }
    }
    start_j = j["current-action"]["start"]["agent"]["x"];
    start_j/=cellsize;
    start_i = j["current-action"]["start"]["agent"]["y"];
    start_i/=cellsize;
    std::cout<<"f";
    cur_goal_j = j["current-action"]["finish"]["agent"]["x"];
    cur_goal_j/=cellsize;
    cur_goal_i = j["current-action"]["finish"]["agent"]["y"];
    cur_goal_i/=cellsize;
    std::cout<<"g";
    goal_j = j["global-finish"]["objects"]["agent"]["x"];
    goal_j/=cellsize;
    goal_i = j["global-finish"]["objects"]["agent"]["y"];
    std::cout<<"h\n";
    goal_i/=cellsize;

    createGrid();
    return true;
}

void JSON_Map::createGrid()
{
    grid.resize(height);
    for(int i = 0; i < height; i++)
        grid[i].resize(width, 0);
    for(int i = 0; i < height; i++)
        for(int j = 0; j < width; j++)
            for(int k = 0; k < obstacles.size(); k++)
                if(obstacles[k].lu_i <= i && obstacles[k].lu_j <= j && obstacles[k].rb_i >= i && obstacles[k].rb_j >= j)
                    grid[i][j] = CN_GC_OBS;

    for(int i = 0; i < height; i++)
    {
        for(int j = 0; j < width; j++)
            std::cout<<grid[i][j]<<" ";
        std::cout<<"\n";
    }
}

bool JSON_Map::CellIsTraversable(int i, int j) const
{
    return (grid[i][j] == CN_GC_NOOBS);
}

bool JSON_Map::CellIsObstacle(int i, int j) const
{
    return (grid[i][j] != CN_GC_NOOBS);
}

bool JSON_Map::CellOnGrid(int i, int j) const
{
    return (i < height && i >= 0 && j < width && j >= 0);
}

bool JSON_Map::lineOfSight(int i1, int j1, int i2, int j2) const
{
    int delta_i = std::abs(i1 - i2);
    int delta_j = std::abs(j1 - j2);
    int step_i = (i1 < i2 ? 1 : -1);
    int step_j = (j1 < j2 ? 1 : -1);
    int error = 0;
    int i = i1;
    int j = j1;
    if(delta_i == 0) {
        for(; j != j2; j += step_j)
            if(CellIsObstacle(i, j))
                return false;
        return true;
    }
    else if(delta_j == 0) {
        for(; i != i2; i += step_i)
            if(CellIsObstacle(i, j))
                return false;
        return true;
    }

    int sep_value = delta_i*delta_i + delta_j*delta_j;
    if(delta_i > delta_j) {
        for(; i != i2; i += step_i) {
            if(CellIsObstacle(i, j))
                return false;
            if(CellIsObstacle(i, j + step_j))
                return false;
            error += delta_j;
            if(error >= delta_i) {
                if(((error << 1) - delta_i - delta_j)*((error << 1) - delta_i - delta_j) < sep_value)
                    if(CellIsObstacle(i + step_i,j))
                        return false;
                if((3*delta_i - ((error << 1) - delta_j))*(3*delta_i - ((error << 1) - delta_j)) < sep_value)
                    if(CellIsObstacle(i, j + 2*step_j))
                        return false;
                j += step_j;
                error -= delta_i;
            }
        }
        if(CellIsObstacle(i, j))
            return false;
    }
    else {
        for(; j != j2; j += step_j) {
            if(CellIsObstacle(i, j))
                return false;
            if(CellIsObstacle(i + step_i, j))
                return false;
            error += delta_i;
            if(error >= delta_j) {
                if(((error << 1) - delta_i - delta_j)*((error << 1) - delta_i - delta_j) < (delta_i*delta_i + delta_j*delta_j))
                    if(CellIsObstacle(i, j + step_j))
                        return false;
                if((3*delta_j - ((error << 1) - delta_i))*(3*delta_j - ((error << 1) - delta_i)) < (delta_i*delta_i + delta_j*delta_j))
                    if(CellIsObstacle(i + 2*step_i, j))
                        return false;
                i += step_i;
                error -= delta_j;
            }
        }
        if(CellIsObstacle(i, j))
            return false;
    }
    return true;
}
