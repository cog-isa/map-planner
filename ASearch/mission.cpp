#include "mission.h"
#include "astar.h"
#include "theta.h"
#include "xmllogger.h"
#include "gl_const.h"

Mission::Mission()
{
    logger = nullptr;
    search = nullptr;
    fileName = nullptr;
}

Mission::Mission(const char *FileName)
{
    fileName = FileName;
    logger = nullptr;
    search = nullptr;
}

Mission::~Mission()
{
    if (logger)
        delete logger;
    if (search)
        delete search;
}

bool Mission::getMap()
{
    return map.getMap(fileName);
}

bool Mission::getConfig()
{
    return true;//config.getConfig(fileName);
}

bool Mission::createLog()
{
    if (logger != NULL) delete logger;
    logger = new XmlLogger(config.LogParams[CN_LP_LEVEL]);
    return logger->getLog(fileName, config.LogParams);
}

void Mission::createEnvironmentOptions()
{
    options = EnvironmentOptions(false,true,false,2);//config.SearchParams[CN_SP_AS], config.SearchParams[CN_SP_AD], config.SearchParams[CN_SP_CC], config.SearchParams[CN_SP_MT]);
}

void Mission::createSearch()
{
    if (search)
       delete search;
    //if (config.SearchParams[CN_SP_ST] == CN_SP_ST_BFS)
    //    search = new BFS();
    //else if (config.SearchParams[CN_SP_ST] == CN_SP_ST_DIJK)
    //    search = new Dijkstra();
    //else if (config.SearchParams[CN_SP_ST] == CN_SP_ST_ASTAR)
    //    search = new Astar(config.SearchParams[CN_SP_HW], config.SearchParams[CN_SP_BT]);
    //else if (config.SearchParams[CN_SP_ST] == CN_SP_ST_JP_SEARCH)
    //    search = new JP_Search(1.0, true);
    //else if (config.SearchParams[CN_SP_ST] == CN_SP_ST_TH)
        search = new Theta(1.0, true);
}

void Mission::startSearch()
{
    sr = search->startSearch(logger, map, options);
}

void Mission::printSearchResultsToConsole()
{

}

void Mission::saveSearchResultsToLog()
{
    JSON_Logger log;
    std::cout<<"Doable:"<<sr.straight_line<<" Target cell:[("<<sr.lu_j<<","<<sr.lu_i<<"),("<<sr.rb_j<<","<<sr.rb_i<<")]\n";
    log.saveLog(fileName,sr.straight_line, sr.lu_i, sr.lu_j, sr.rb_i, sr.rb_j);
    /*logger->writeToLogSummary(sr.numberofsteps, sr.nodescreated, sr.pathlength, sr.time, map.cellsize);
    if (sr.pathfound) {
        logger->writeToLogPath(*sr.lppath);
        logger->writeToLogHPpath(*sr.hppath);
        //logger->writeToLogMap(map, *sr.lppath);
    } else
        logger->writeToLogNotFound();
    logger->saveLog();*/
}

const char *Mission::getAlgorithmName()
{
    if (config.SearchParams[CN_SP_ST] == CN_SP_ST_ASTAR)
        return CNS_SP_ST_ASTAR;
    else if (config.SearchParams[CN_SP_ST] == CN_SP_ST_DIJK)
        return CNS_SP_ST_DIJK;
    else if (config.SearchParams[CN_SP_ST] == CN_SP_ST_BFS)
        return CNS_SP_ST_BFS;
    else if (config.SearchParams[CN_SP_ST] == CN_SP_ST_JP_SEARCH)
        return CNS_SP_ST_JP_SEARCH;
    else if (config.SearchParams[CN_SP_ST] == CN_SP_ST_TH)
        return CNS_SP_ST_TH;
    else
        return "";
}
