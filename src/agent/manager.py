import multiprocessing
import time
import importlib
from multiprocessing import Process

class Manager:
    def __init__(self, problem, agpath = 'mapspatial.agent.agent_search', backward = True, subsearch = 'greedy'):
        self.problem = problem
        self.solution = []
        self.finished = None
        self.agtype = 'SpAgent'
        self.agpath = agpath
        self.ref = 1
        self.backward = backward
        self.subsearch = subsearch

    def agent_start(self, agent):
        """
        Function that send task to agent
        :param agent: I
        :return: flag that task accomplished
        """
        import logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("process-%r" % (agent.name))
        logger.info('Agent {0} start planning'.format(agent.name))
        saved = agent.search_solution()
        if saved:
            logger.info('Agent {0} finish planning'.format(agent.name))
            self.finished = True
        return agent.name +' finished'

    def manage_agent(self):
        """
        Create a separate process for the agent
        :return: the best solution
        """
        class_ = getattr(importlib.import_module(self.agpath), self.agtype)
        workman = class_()
        workman.initialize(self.problem, self.ref, self.problem.task_file,  self.backward, self.subsearch)
        multiprocessing.set_start_method('spawn')
        ag = Process(target=self.agent_start, args = (workman, ))
        ag.start()
        ag.join()
        if self.solution:
            return self.solution
        else:
            time.sleep(1)

        return None

















