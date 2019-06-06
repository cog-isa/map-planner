import logging
import os

SOLUTION_FILE_SUFFIX = '.soln'

import platform

if platform.system() != 'Windows':
    delim = '/'
else:
    delim = '\\'

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("process-main")

class MapPlanner():
    def __init__(self, **kwargs):
        kwgs = kwargs['Settings']
        self.agtype = kwgs['agtype']
        self.agpath = kwgs['agpath']
        self.TaskType = kwgs['tasktype']
        self.domain, self.problem = self.find_domain(kwgs['path'], kwgs['task'])
        self.refinement = eval(kwgs['refinement_lv'])
        self.backward = eval(kwgs['backward'])
        logger.info('MAP algorithm has started...')

    def search_upper(self, path, file):
        """
        Recursive domain search
        :param path: path to the current task
        :param file: domain name
        :return: full path to the domain
        """
        if not file in os.listdir(path):
            new_path = delim
            for element in path.split(delim)[1:-2]:
                new_path+=element + delim
            return self.search_upper(new_path, file)
        else:
            return path + delim + file


    def find_domain(self, path, number):
        """
        Domain search function
        :param path: path to current task
        :param number: task number
        :return:
        """
        ext = '.pddl'
        if self.TaskType == 'htn':
            ext = '.hddl'
        domain = 'domain' + ext
        task = 'task' + number + ext
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

    def _parse(self, domain_file, problem_file):
        """
        pddl Parser
        :param domain_file:
        :param problem_file:
        :return:
        """
        from mapcore.pddl.parser import Parser

        parser = Parser(domain_file, problem_file)
        logging.info('Parsing Domain {0}'.format(domain_file))
        domain = parser.parse_domain()
        logging.info('Parsing Problem {0}'.format(problem_file))
        problem = parser.parse_problem(domain)
        logging.debug(domain)
        logging.info('{0} Predicates parsed'.format(len(domain.predicates)))
        logging.info('{0} Actions parsed'.format(len(domain.actions)))
        logging.info('{0} Objects parsed'.format(len(problem.objects)))
        logging.info('{0} Constants parsed'.format(len(domain.constants)))
        return problem

    def search_classic(self):
        """
        classic PDDL-based plan search search
        :return: the final solution
        """
        from mapcore.agent.manager import Manager

        problem = self._parse(self.domain, self.problem)
        logger.info('Parsing was finished...')
        manager = Manager(problem, self.agpath, self.agtype, backward=self.backward)
        solution = manager.manage_agent()
        return solution

    def search_htn(self):
        """
        classic HTN-based plan search
        :return: the final solution
        """
        from mapcore.hddl.hddl_parser import HTNParser
        from mapcore.grounding.hddl_grounding import ground
        from mapcore.search.htnsearch import HTNSearch
        parser = HTNParser(self.domain, self.problem)
        logging.info('Parsing was finished...')
        logging.info('Parsing Domain {0}'.format(self.domain))
        domain = parser.ParseDomain(parser.domain)
        logging.info('Parsing Problem {0}'.format(self.problem))
        problem = parser.ParseProblem(parser.problem)
        logging.info('{0} Objects parsed'.format(len(problem['objects'])))
        logging.info('{0} Predicates parsed'.format(len(domain['predicates'])))
        logging.info('{0} Actions parsed'.format(len(domain['actions'])))
        logging.info('{0} Methods parsed'.format(len(domain['methods'])))
        signs = ground(domain, problem)
        logging.info('{0} Signs created'.format(len(signs)))
        htn = HTNSearch(signs)
        solution = htn.search_plan()
        return solution

    def search(self):
        if self.TaskType == 'classic':
            return self.search_classic()
        elif self.TaskType == 'htn':
            return self.search_htn()
        else:
            raise Exception('Tasks can be classic or htn!!!')