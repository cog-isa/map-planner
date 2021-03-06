import argparse
import logging
import os
import re
import sys
import time

from .grounding import sign_grounding
from .pddl.parser import Parser
from .search.mapsearch import map_search

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


def _ground(problem, is_load):
    logging.info('Grounding start: {0}'.format(problem.name))
    task = sign_grounding.ground(problem)
    if is_load:
        task.load_signs()
    logging.info('Grounding end: {0}'.format(problem.name))
    logging.info('{0} Signs created'.format(len(task.signs)))
    return task


def search_plan(domain_file, problem_file, save, load):
    problem = _parse(domain_file, problem_file)
    task = _ground(problem, load)

    search_start_time = time.clock()
    logging.info('Search start: {0}'.format(task.name))
    solution = map_search(task)
    logging.info('Search end: {0}'.format(task.name))
    logging.info('Wall-clock search time: {0:.2}'.format(time.clock() -
                                                         search_start_time))

    if save:
        task.save_signs(solution)

    return solution


if __name__ == '__main__':
    # Commandline parsing
    log_levels = ['debug', 'info', 'warning', 'error']

    argparser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument(dest='domain', nargs='?')
    argparser.add_argument(dest='problem')
    argparser.add_argument('-l', '--loglevel', choices=log_levels,
                           default='info')
    argparser.add_argument('-s', '--save', action='store_true')
    argparser.add_argument('-w', '--load', action='store_true')

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

    solution = search_plan(args.domain, args.problem, args.save, args.load)

    if solution is None:
        logging.warning('No solution could be found')
    else:
        solution_file = args.problem + SOLUTION_FILE_SUFFIX
        logging.info('Plan length: %s' % len(solution))
        with open(solution_file, 'w') as file:
            for name, op in solution:
                print(name, op, file=file)
