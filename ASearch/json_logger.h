#ifndef JSON_LOGGER_H
#define JSON_LOGGER_H
#include "json.hpp"
#include <fstream>
#include <iostream>
#include <cstdlib>
using namespace nlohmann;

class JSON_Logger
{
public:
    JSON_Logger();
    bool saveLog(std::string inputName, bool answer, int lu_i, int lu_j, int rb_i, int rb_j);
};

#endif // JSON_LOGGER_H
