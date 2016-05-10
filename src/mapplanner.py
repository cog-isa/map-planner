import argparse
import logging
import os
import re
import sys
import time

from grounding import sign_grounding
from pddl.parser import Parser
from search.mapsearch import map_search

NUMBER = re.compile(r'\d+')
i = 0


def find_domain(problem):
    """
    This function tries to guess a domain file from a given problem file.
    It first uses a file called "domain.pddl" in the same directory as
    the problem file. If the problem file's name contains digits, the first
    group of digits is interpreted as a number and the directory is searched
    for a file that contains both, the word "domain" and the number.
    This is conforming to some domains where there is a special domain file
    for each problem, e.g. the airport domain.

    @param problem    The pathname to a problem file
    @return A valid name of a domain
    """
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


def _ground(problem):
    logging.info('Grounding start: {0}'.format(problem.name))
    task = sign_grounding.ground(problem)
    logging.info('Grounding end: {0}'.format(problem.name))
    logging.info('{0} Signs created'.format(len(task.signs)))
    return task


def search_plan(domain_file, problem_file):
    """
    Parses the given input files to a specific planner task and then tries to
    find a solution using the specified  search algorithm and heuristics.

    @param domain_file      The path to a domain file
    @param problem_file     The path to a problem file in the domain given by
                            domain_file
    @return A list of actions that solve the problem
    """
    problem = _parse(domain_file, problem_file)
    task = _ground(problem)

    search_start_time = time.clock()
    logging.info('Search start: {0}'.format(task.name))
    solution = map_search(task)
    logging.info('Search end: {0}'.format(task.name))
    logging.info('Wall-clock search time: {0:.2}'.format(time.clock() -
                                                         search_start_time))

    return solution


def _write_solution(solution, filename):
    assert solution is not None
    with open(filename, 'w') as file:
        for name, op in solution:
            print(name, op, file=file)


if __name__ == '__main__':
    # Commandline parsing
    log_levels = ['debug', 'info', 'warning', 'error']

    argparser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument(dest='domain', nargs='?')
    argparser.add_argument(dest='problem')
    argparser.add_argument('-l', '--loglevel', choices=log_levels,
                           default='info')
    argparser.add_argument('-i', '--iter', default=1, type=int)

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
    for _ in range(args.iter):
        solution = search_plan(args.domain, args.problem)

        if solution is None:
            logging.warning('No solution could be found')
        else:
            solution_file = args.problem + '.soln'
            logging.info('Plan length: %s' % len(solution))
            _write_solution(solution, solution_file)
            i += 1
    logging.info('plan have been found for %s times from %s iterations' % (i, args.iter))
