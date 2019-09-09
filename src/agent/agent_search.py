import logging
import time

from mapcore.grounding import pddl_grounding
from mapcore.search.mapsearch import MapSearch
from mapcore.grounding.sign_task import Task
from mapcore.grounding import hddl_grounding


class Agent:
    def __init__(self):
        pass

    # Initialization
    def initialize(self, problem, TaskType, backward):
        """
        This function allows agent to be initialized. We do not use basic __init__ to let
        user choose a valid variant of agent. You can take agent with othe abilities.
        :param problem: problem
        :param ref: the dynamic value of plan clarification
        """
        try:
            self.name = [el[0] for el in problem.objects if el[1] == 'agent'][0]
        except IndexError:
            self.name = 'I'
        self.problem = problem
        self.solution = []
        self.final_solution = ''
        self.backward = backward
        self.TaskType = TaskType

    # Grounding tasks
    def load_sw(self):
        """
        This functions is needed to load SWM.
        :return: task - sign representation of the problem.
        """
        logging.info('Grounding start: {0}'.format(self.problem.name))
        signs = Task.load_signs(self.name)
        if self.TaskType == 'hddl':
            task = hddl_grounding.ground(self.problem, self.name, signs)
        else:
            task = pddl_grounding.ground(self.problem, self.name, signs)
        logging.info('Grounding end: {0}'.format(self.problem.name))
        logging.info('{0} Signs created'.format(len(task.signs)))
        return task

    def search_solution(self):
        """
        This function is needed to synthesize all plans, choose the best one and
        save the experience.
        """
        task = self.load_sw()
        logging.info('Search start: {0}, Start time: {1}'.format(task.name, time.clock()))
        search = MapSearch(task, self.TaskType, self.backward)
        solutions, goal = search.search_plan()
        if goal:
            task.goal_situation = goal
        self.solution = search.long_relations(solutions)
        if self.backward:
            self.solution = list(reversed(self.solution))
        file_name = task.save_signs(self.solution)
        if file_name:
            logging.info('Agent ' + self.name + ' finished all works')

