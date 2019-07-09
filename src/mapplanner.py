import logging
import os
import json
from mapcore.mapplanner import MapPlanner as MPcore
from mapspatial.agent.manager import Manager

SOLUTION_FILE_SUFFIX = '.soln'

import platform

if platform.system() != 'Windows':
    delim = '/'
else:
    delim = '\\'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("process-main")

class MapPlanner(MPcore):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.subsearch = kwargs['Settings']['subsearch']
        #self.domain, self.problem = self.find_domain(self.kwgs['path'], self.kwgs['task'])

    def find_domain(self, path, number):
        """
        Domain search function
        :param path: path to current task
        :param number: task number
        :return:
        """
        if self.TaskType == 'spatial':
            ext = '.json'
            path += 'task' + number + delim
        elif self.TaskType == 'htn':
            ext = '.hddl'
        else:
            ext = '.pddl'
        task = 'task' + number + ext
        domain = 'domain' + ext

        if not domain in os.listdir(path):
            domain2 = self.search_upper(path, domain)
            if not domain2:
                raise Exception('domain not found!')
            else:
                domain = domain2
        else:
            domain = path + domain
        if not task in os.listdir(path):
            raise Exception('task not found!')
        else:
            problem = path + task

        return domain, problem

    def search_spatial(self):
        """
        spatial plan search
        :return: the final solution with cell coordinates
        """
        from mapspatial.grounding.json_grounding import Problem
        logging.info('Parsing Problem {0}'.format(self.problem))
        with open(self.problem) as data_file1:
            problem_parsed = json.load(data_file1)
        logging.info('Parsing Domain {0}'.format(self.domain))
        with open(self.domain) as data_file2:
            signs_structure = json.load(data_file2)

        logging.info('{0} Objects parsed'.format(len(problem_parsed['global-start']['objects'])))
        logging.info('{0} Predicates parsed'.format(len(signs_structure['predicates'])))
        logging.info('{0} Actions parsed'.format(len(signs_structure['actions'])))
        logging.info('Map contain {0} walls'.format(len(problem_parsed['map']['wall'])))
        logging.info('Map size is {0}:{1}'.format(problem_parsed['map']['map-size'][0], problem_parsed['map']['map-size'][1]))
        problem = Problem(signs_structure, problem_parsed, self.problem, None)
        logger.info('Parsing was finished...')
        manager = Manager(problem, self.agpath, backward=self.backward, subsearch = self.subsearch)
        solution = manager.manage_agent()
        return solution


    def search(self):
        if self.TaskType == 'classic':
            return self.search_classic()
        elif self.TaskType == 'htn':
            return self.search_htn()
        elif self.TaskType == 'spatial':
            return self.search_spatial()
        else:
            raise Exception('Tasks can be classic or htn!!!')