#include "mission.h"

int main(int argc, char* argv[])
{
    if(argc < 2) {
        return 0;
    }
    Mission mission(argv[1]);
    if(!mission.getMap()) {
    }
    else {
        if(!mission.getConfig())
            std::cout<<"Incorrect configurations! Program halted!"<<std::endl;
        else {

            /*if(!mission.createLog())
                std::cout<<"Log chanel has not been created! Program halted!"<<std::endl;
            else*/{
                mission.createEnvironmentOptions();
                mission.createSearch();
                mission.startSearch();
                //mission.printSearchResultsToConsole();
                mission.saveSearchResultsToLog();
            }
        }
    }
    return 0;
}

