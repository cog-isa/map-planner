import argparse
import logging
import os
import re
import sys
import time
import logging
from pddl.parser import Parser

from grounding.agent_grounding import Agent


NUMBER = re.compile(r'\d+')
SOLUTION_FILE_SUFFIX = '.soln'


def find_domain(problem):
    dir, name = os.path.split(problem)
    number_match = NUMBER.search(name)
    number = number_match.group(0)
    domain = os.path.join(dir, 'domain.pddl')
    for file in os.listdir(dir):
        if 'domain' in file and number in file:
            domain = os.path.join(dir, file)
            break
    if not os.path.isfile(domain):
        logging.error('Domain file "{0}" can not be found'.format(domain))
        sys.exit(1)
    logging.info('Found domain {0}'.format(domain))
    return domain


def _parse(domain_file, problem_file):
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

#
# from memory_profiler import profile
#
# @profile
def search_plan(domain_dir, problem_numb, saveload):
    from os import listdir
    agent_tasks = []
    if len(problem_numb) == 1:
        problem_numb = "0"+problem_numb
    for domain in [file for file in listdir(domain_dir) if "domain" in file.lower()]:
        agent_tasks.append([domain_dir+"/"+domain, domain_dir+"/task"+problem_numb +".pddl"])

    agents = []
    solutions = []
    for domain_file, problem_file in agent_tasks:
        problem = _parse(domain_file, problem_file)
        for obj in problem.objects:
            if problem.objects[obj].name == 'agent':
                agents.append(obj)

    for agent in agents:
        agent = Agent(agent, problem, saveload)
        solution = agent.search_solution()
        solutions.append(solution)




    return solutions



if __name__ == '__main__':
    # Commandline parsing
    log_levels = ['debug', 'info', 'warning', 'error']

    argparser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument(dest='domain', nargs='?')
    argparser.add_argument(dest='problem_numb')
    argparser.add_argument('-l', '--loglevel', choices=log_levels,
                           default='info')
    argparser.add_argument('-s', '--saveload', action='store_true')

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

    # args.problem = os.path.abspath(args.problem)
    if args.domain is None:
        args.domain = find_domain(args.problem_numb)
    else:
        args.domain = os.path.abspath(args.domain)


    solutions = search_plan(args.domain, args.problem_numb, args.saveload)

    if solutions is None:
        logging.warning('No solution could be found')
    else:
        solution_file = args.domain + SOLUTION_FILE_SUFFIX
        for solution  in solutions:
            logging.info('Plan length: %s' % len(solution))
        with open(solution_file, 'w') as file:
            for solution in solutions:
                for op, name, agent in solution:
                    print(op, name,agent, file=file)
