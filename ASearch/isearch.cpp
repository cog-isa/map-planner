#include "isearch.h"
#include <vector>
#include <math.h>
#include <limits>
#include <chrono>

ISearch::ISearch()
{
    hweight = 1;
    breakingties = CN_SP_BT_GMAX;
    openSize = 0;
}

ISearch::~ISearch(void) {}

bool ISearch::stopCriterion()
{
    if (openSize == 0) {
        std::cout << "OPEN list is empty!" << std::endl;
        return true;
    }
    return false;
}

SearchResult ISearch::startSearch(ILogger *Logger, const JSON_Map &map, const EnvironmentOptions &options)
{
    if(map.lineOfSight(map.start_i, map.start_j, map.cur_goal_i, map.cur_goal_j))
        sresult.straight_line = true;
    else
        sresult.straight_line = false;

    if(map.lineOfSight(map.start_i, map.start_j, map.goal_i, map.goal_j))
    {
        sresult.lu_i = map.goal_i*map.cellsize;
        sresult.lu_j = map.goal_j*map.cellsize;
        sresult.rb_i = (map.goal_i + 1)*map.cellsize-1;
        sresult.rb_j = (map.goal_j + 1)*map.cellsize-1;
    }
    open.resize(map.height);
    Node curNode;
    curNode.i = map.start_i;
    curNode.j = map.start_j;
    curNode.g = 0;
    curNode.H = computeHFromCellToCell(curNode.i, curNode.j, map.goal_i, map.goal_j, options);
    curNode.F = hweight * curNode.H;
    curNode.parent = nullptr;
    addOpen(curNode);
    int closeSize = 0;
    bool pathfound = false;
    while (!stopCriterion()) {
        curNode = findMin();
        close.insert({curNode.i * map.width + curNode.j, curNode});
        closeSize++;
        open[curNode.i].pop_front();
        openSize--;
        if (curNode.i == map.goal_i && curNode.j == map.goal_j) {
            pathfound = true;
            break;
        }
        std::list<Node> successors = findSuccessors(curNode, map, options);
        std::list<Node>::iterator it = successors.begin();
        auto parent = &(close.find(curNode.i * map.width + curNode.j)->second);
        while (it != successors.end()) {
            it->parent = parent;
            it->H = computeHFromCellToCell(it->i, it->j, map.goal_i, map.goal_j, options);
            *it = resetParent(*it, *it->parent, map, options);
            it->F = it->g + hweight * it->H;
            addOpen(*it);
            it++;
        }
    }
    makePrimaryPath(curNode);
    Node target = *(++hppath.begin());
    sresult.lu_i = target.i*map.cellsize;
    sresult.lu_j = target.j*map.cellsize;
    sresult.rb_i = (target.i + 1)*map.cellsize-1;
    sresult.rb_j = (target.j + 1)*map.cellsize-1;
    return sresult;
}

Node ISearch::findMin()
{
    Node min;
    min.F = std::numeric_limits<double>::infinity();
    for (int i = 0; i < open.size(); i++)
        if (!open[i].empty() && open[i].begin()->F <= min.F)
            if (open[i].begin()->F == min.F){
                if((breakingties == CN_SP_BT_GMAX && open[i].begin()->g >= min.g) ||
                   (breakingties == CN_SP_BT_GMIN && open[i].begin()->g <= min.g))
                    min = *open[i].begin();
            }
            else
                min = *open[i].begin();
    return min;
}

std::list<Node> ISearch::findSuccessors(Node curNode, const JSON_Map &map, const EnvironmentOptions &options)
{
    Node newNode;
    std::list<Node> successors;
    for (int i = -1; i <= +1; i++)
        for (int j = -1; j <= +1; j++)
            if ((i != 0 || j != 0) && map.CellOnGrid(curNode.i + i, curNode.j + j) &&
                    (map.CellIsTraversable(curNode.i + i, curNode.j + j))) {
                if (i != 0 && j != 0) {
                    if (!options.allowdiagonal)
                        continue;
                    else if (!options.cutcorners) {
                        if (map.CellIsObstacle(curNode.i, curNode.j + j) ||
                                map.CellIsObstacle(curNode.i + i, curNode.j))
                            continue;
                    }
                    else if (!options.allowsqueeze) {
                        if (map.CellIsObstacle(curNode.i, curNode.j + j) &&
                                map.CellIsObstacle(curNode.i + i, curNode.j))
                            continue;
                    }
                }
                if (close.find((curNode.i + i) * map.width + curNode.j + j) == close.end()) {
                    newNode.i = curNode.i + i;
                    newNode.j = curNode.j + j;
                    if(i == 0 || j == 0)
                        newNode.g = curNode.g + 1;
                    else
                        newNode.g = curNode.g + sqrt(2);
                    successors.push_front(newNode);
                }
            }
    return successors;
}

void ISearch::makePrimaryPath(Node curNode)
{
    Node current = curNode;
    while (current.parent) {
        lppath.push_front(current);
        current = *current.parent;
    }
    lppath.push_front(current);
}

void ISearch::makeSecondaryPath()
{
    std::list<Node>::const_iterator iter = lppath.begin();
    int curI, curJ, nextI, nextJ, moveI, moveJ;
    hppath.push_back(*iter);
    while (iter != --lppath.end()) {
        curI = iter->i;
        curJ = iter->j;
        ++iter;
        nextI = iter->i;
        nextJ = iter->j;
        moveI = nextI - curI;
        moveJ = nextJ - curJ;
        ++iter;
        if ((iter->i - nextI) != moveI || (iter->j - nextJ) != moveJ)
            hppath.push_back(*(--iter));
        else
            --iter;
    }
}

void ISearch::addOpen(Node newNode)
{
    std::list<Node>::iterator iter, pos;

    if (open[newNode.i].size() == 0) {
        open[newNode.i].push_back(newNode);
        openSize++;
        return;
    }

    pos = open[newNode.i].end();
    bool posFound = false;
    for (iter = open[newNode.i].begin(); iter != open[newNode.i].end(); ++iter) {
        if (!posFound && iter->F >= newNode.F)
            if (iter->F == newNode.F) {
                if((breakingties == CN_SP_BT_GMAX && newNode.g >= iter->g) ||
                   (breakingties == CN_SP_BT_GMIN && newNode.g <= iter->g)) {
                    pos=iter;
                    posFound=true;
                }
            }
            else {
                pos = iter;
                posFound = true;
            }

        if (iter->j == newNode.j) {
            if (newNode.F >= iter->F)
                return;
            else {
                if (pos == iter) {
                    iter->F = newNode.F;
                    iter->g = newNode.g;
                    iter->parent = newNode.parent;
                    return;
                }
                open[newNode.i].erase(iter);
                openSize--;
                break;
            }
        }
    }
    openSize++;
    open[newNode.i].insert(pos, newNode);
}
