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
# def _ground(problem, is_load):
#     logging.info('Grounding start: {0}'.format(problem.name))
#     task = sign_grounding.ground(problem)
#     if is_load:
#         task.load_signs()
#     logging.info('Grounding end: {0}'.format(problem.name))
#     logging.info('{0} Signs created'.format(len(task.signs)))
#     return task


def search_plan(domain_dir, problem_dir, saveload):
    from os import listdir
    agent_tasks = []
    for domain in [file for file in listdir(domain_dir) if "domain" in file.lower()]:
        for problem in [file for file in listdir(problem_dir) if "task" in file.lower()]:
            agent_tasks.append([domain_dir+"/"+domain, problem_dir+"/"+problem])

    agents = []
    for domain_file, problem_file in agent_tasks:
        problem = _parse(domain_file, problem_file)
        for obj in problem.objects:
            if problem.objects[obj].name == 'agent':
                agents.append(obj)

    for agent in agents:
        agent = Agent(agent, problem, saveload)
        solution = agent.search_solution()



    # if saveload:
    #     task.save_signs(solution)
    #
    # return solution


if __name__ == '__main__':
    # Commandline parsing
    log_levels = ['debug', 'info', 'warning', 'error']

    argparser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument(dest='domain', nargs='?')
    argparser.add_argument(dest='problem')
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

    args.problem = os.path.abspath(args.problem)
    if args.domain is None:
        args.domain = find_domain(args.problem)
    else:
        args.domain = os.path.abspath(args.domain)

    solution = search_plan(args.domain, args.problem, args.saveload)

    if solution is None:
        logging.warning('No solution could be found')
    else:
        solution_file = args.problem + SOLUTION_FILE_SUFFIX
        logging.info('Plan length: %s' % len(solution))
        with open(solution_file, 'w') as file:
            for name, op in solution:
                print(name, op, file=file)
