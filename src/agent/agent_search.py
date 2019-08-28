import logging
import sys
import time

from mapspatial.grounding import json_grounding
from mapspatial.search.mapsearch import SpSearch
from mapcore.grounding.sign_task import Task


class SpAgent:
    def __init__(self):
        pass

    # Initialization
    def initialize(self, name, agents, problem, backward, subsearch):
        """
        This function allows agent to be initialized. We do not use basic __init__ to let
        user choose a valid variant of agent. You can take agent with othe abilities.
        :param problem: problem
        :param ref: the dynamic value of plan clarification
        """
        self.name = name
        self.agents = agents
        self.problem = problem
        self.solution = []
        self.final_solution = ''
        self.backward = backward
        self.task_file = problem.task_file
        self.subsearch = subsearch
        self.task = None


    # Grounding tasks
    def loadSWM(self):
        """
        This functions is needed to load SWM.
        :return: task - sign representation of the problem.
        """
        logging.info('Grounding start: {0}'.format(self.problem.name))
        signs = Task.load_signs(self.name)
        self.task = json_grounding.spatial_ground(self.problem, self.name, self.agents, signs, self.backward)
        logging.info('Grounding end: {0}'.format(self.problem.name))
        logging.info('{0} Signs created'.format(len(self.task.signs)))
        if signs:
            return len(self.task.signs) - len(signs)
        else:
            return 0

    def search_solution(self):
        """
        This function is needed to synthesize all plans, choose the best one and
        save the experience.
        """
        logging.info('Search start: {0}, Start time: {1}'.format(self.task.name, time.clock()))
        search = SpSearch(self.task, self.task_file, self.backward, self.subsearch)
        solutions = search.search_plan()
        if not solutions:
            print("Can't find plan. Try to change planner conditions!")
            sys.exit(1)
        self.solution = search.long_relations(solutions)
        file_name = self.task.save_signs(self.solution)
        if file_name:
            logging.info('Agent ' + self.name + ' finished all works')

