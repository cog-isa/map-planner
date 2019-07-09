#-------------------------------------------------
#
# Project created by QtCreator 2011-02-26T12:08:02
#
#-------------------------------------------------

TARGET = ASearch
CONFIG   += console
CONFIG   -= app_bundle
TEMPLATE = app
QMAKE_CXXFLAGS += -std=c++11 -O2 -Wall -Wextra

win32 {
QMAKE_LFLAGS += -static -static-libgcc -static-libstdc++
}

SOURCES += \
    tinyxml2.cpp \
    xmllogger.cpp \
    isearch.cpp \
    mission.cpp \
    map.cpp \
    config.cpp \
    astar.cpp \
    asearch.cpp \
    jp_search.cpp \
    theta.cpp \
    environmentoptions.cpp \
    json_map.cpp \
    json_logger.cpp

HEADERS += \
    tinyxml2.h \
    node.h \
    gl_const.h \
    xmllogger.h \
    isearch.h \
    mission.h \
    map.h \
    ilogger.h \
    config.h \
    astar.h \
    searchresult.h \
    jp_search.h \
    theta.h \
    environmentoptions.h \
    json.hpp \
    json_map.h \
    json_logger.h
