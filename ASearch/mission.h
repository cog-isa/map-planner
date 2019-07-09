#ifndef MISSION_H
#define	MISSION_H

#include "map.h"
#include "config.h"
#include "isearch.h"
#include "ilogger.h"
#include "searchresult.h"
#include "environmentoptions.h"
#include "jp_search.h"
#include "astar.h"
#include "theta.h"
#include "xmllogger.h"
#include "json_map.h"
#include "json_logger.h"

class Mission
{
    public:
        Mission();
        Mission (const char* fileName);
        ~Mission();

        bool getMap();
        bool getConfig();
        bool createLog();
        void createSearch();
        void createEnvironmentOptions();
        void startSearch();
        void printSearchResultsToConsole();
        void saveSearchResultsToLog();

    private:
        const char* getAlgorithmName();

        JSON_Map                map;
        Config                  config;
        EnvironmentOptions      options;
        ISearch*                search;
        ILogger*                logger;
        const char*             fileName;
        SearchResult            sr;
};

#endif

