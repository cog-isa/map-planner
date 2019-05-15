#include "json_logger.h"

JSON_Logger::JSON_Logger()
{

}

bool JSON_Logger::saveLog(std::string inputName, bool answer, int lu_i, int lu_j, int rb_i, int rb_j)
{
    auto it = inputName.find("requests");
    std::string respfolder = "mkdir "+inputName.substr(0, it) +"responses";
    system(respfolder.c_str());
    inputName.replace(it, 8, "responses");
    it = inputName.find("request_");
    inputName.replace(it, 7, "result");
    json j;
    j["result"]["doable"] = answer;
    j["result"]["target-cell"][0] = lu_j;
    j["result"]["target-cell"][1] = lu_i;
    j["result"]["target-cell"][2] = rb_j;
    j["result"]["target-cell"][3] = rb_i;
    std::ofstream file(inputName);
    file << j;
    file.close();
    return true;
}
