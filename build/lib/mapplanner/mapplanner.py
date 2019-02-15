import argparse
import logging
import os
import json

from mapplanner.grounding.json_grounding import Problem
from mapplanner.pddl.parser import Parser
from mapplanner.agent.manager import Manager

SOLUTION_FILE_SUFFIX = '.soln'

class MapPlanner():
    def __init__(self, **kwargs):

        kwgs = kwargs['Settings']

        self.LogicType = kwgs['LogicType']
        self.is_load = kwgs['is_load']
        self.gazebo = eval(kwgs['gazebo'])
        self.LogicalSearch = kwgs['LogicalSearch']
        self.agtype = kwgs['agtype']
        self.agpath = kwgs['agpath']
        self.domain, self.problem = self.clarify_problem(kwgs['path'], kwgs['task'], self.LogicType)
        self.refinement = eval(kwgs['refinement_lv'])

        logging.info('multiMAP ready to plan')
    def searcher(self):
        return self.find_solution(self.domain, self.problem, self.LogicType, self.is_load, self.gazebo, self.LogicalSearch)

    def search_upper(self, path, file, delim):
        if not file in os.listdir(path):
            new_path = '/'
            for element in path.split(delim)[1:-2]:
                new_path+=element + delim
            return self.search_upper(new_path, file, delim)
        else:
            return path + delim + file


    def clarify_problem(self, path, number, logic):
        domain = ''
        task = ''
        if logic == 'spatial':
            domain = 'domain.json'
            task = 'task' + number + '.json'
        elif logic == 'classic':
            domain = 'domain.pddl'
            task = 'task' + number + '.pddl'
        if not domain in os.listdir(path):
            import platform
            if platform.system() != 'Windows':
                delim = '/'
            else:
                delim = '\\'
            domain2 = self.search_upper(path, domain, delim)
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
        # Parsing
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

    def agent_manager(self, agents, problem, logic, saveload, gazebo = False, LogicalSearch = ''):
        manager = Manager(agents, problem, logic, saveload, gazebo, LogicalSearch,self.agpath, self.agtype, self.refinement)
        solution = manager.manage_agents()
        return solution

    def search_classic(self, domain_file, problem_file, logic, saveload):
        def action_agents(problem):
            agents = set()
            for _, action in problem.domain.actions.items():
                for ag in action.agents:
                    for obj, type in problem.objects.items():
                        if type.name == ag:
                            agents.add(obj)
            return agents

        problem = self._parse(domain_file, problem_file)
        act_agents = action_agents(problem)
        logging.info('Agents found in actions: {0}'.format(len(act_agents)))
        agents = set()
        if problem.constraints:
            if len(act_agents):
                agents |= act_agents
            else:
                for constr in problem.constraints:
                    agents.add(constr)
                logging.info('Agents found in constraints: {0}'.format(len(agents)))
        elif act_agents:
            agents |= act_agents
        else:
            agents.add('I')
            logging.info('Only 1 agent plan')


        solution = self.agent_manager(agents, problem, logic, saveload)
        return solution

    def search_spatial(self, domain_file, problem_file, logic = 'spatial', saveload = False, gazebo = False, LogicalSearch=''):

        with open(problem_file) as data_file1:
            problem_parsed = json.load(data_file1)
        with open(domain_file) as data_file2:
            signs_structure = json.load(data_file2)

        problem = Problem(signs_structure, problem_parsed, None)

        return self.agent_manager(problem_parsed['agents'], problem, logic, saveload, gazebo, LogicalSearch)

    def find_solution(self, domain, problem, LogicType, saveload, gazebo, LogicalSearch = ''):
        if LogicType == 'spatial':
            solution = self.search_spatial(domain, problem, LogicType, saveload, gazebo, LogicalSearch)
        elif LogicType == 'classic':
            if gazebo:
                raise Exception('Only spatial logic support gazebo visualization!')
            solution = self.search_classic(domain, problem, LogicType, saveload)
        else:
            raise Exception('Logic type %s is not supported!' % LogicType)
        return solution

if __name__ == '__example__':

    # Commandline parsing. Just Example of work!
    # Do not start!

    log_levels = ['debug', 'info', 'warning', 'error']
    logic_type = ['spatial', 'classic']

    argparser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument(dest='benchmark')
    argparser.add_argument(dest='task_number')
    argparser.add_argument('-g', '--gazebo', action='store_true')
    argparser.add_argument('-l', '--loglevel', choices=log_levels,
                           default='info')
    argparser.add_argument('-lt', '--LogicType', choices=logic_type,
                           default='spatial')
    argparser.add_argument('-s', '--save', action='store_true')
    argparser.add_argument('-st', '--LogicalSearch')

    args = argparser.parse_args()

    rootLogger = logging.getLogger()
    logFormatter = logging.Formatter("%(asctime)s %(levelname)-8s  %(message)s")
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    rootLogger.addHandler(consoleHandler)
    fileHandler = logging.FileHandler('pmaplanner.log')
    fileHandler.setFormatter(logFormatter)
    rootLogger.addHandler(fileHandler)
    rootLogger.setLevel(args.loglevel.upper())

    planner = MapPlanner(args.benchmark, args.task_number)

    solution = planner.searcher()


    if solution is None:
        logging.warning('No solution could be found')
    else:
        solution_file = str(args.benchmark) + '_task'+args.task_number + SOLUTION_FILE_SUFFIX

        with open(solution_file, 'w') as file:
            if ' && ' in solution:
                logging.info('Plan length: %s' % len(solution.split(' && ')[:-1]))
                for action in solution.split(' && ')[:-1]:
                    print(action, file=file)
            else:
                logging.info('Plan length: %s' % len(solution.split(';')[:-1]))
                for action in solution.split(';')[:-1]:
                    print(action, file=file)

