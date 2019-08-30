import importlib
import logging
from multiprocessing import Pipe, Process

from mapmulti.agent.agent_search import DecisionStrategies

def agent_activation(agpath, agtype, name, agents, problem, backward, subsearch, childpipe):
    # init agent
    class_ = getattr(importlib.import_module(agpath), agtype)
    workman = class_()
    workman.initialize(name, agents, problem, backward, subsearch)
    # load SWM and calculate the amount of new signs
    new_signs = workman.loadSWM()
    childpipe.send((name, new_signs))
    # load info about the major agent
    major_agent = childpipe.recv()

    # search scenario
    ##### todo create pddl automatically

    task_paths = problem.task_file.split('/')[1:-1]
    import os
    domain_file = os.getcwd()+'/src/benchmarks/maspatial/'+task_paths[-1]+'/scenario/domain.pddl'
    task_file = os.getcwd() + '/src/benchmarks/maspatial/' + task_paths[-1] + '/scenario/'+task_paths[-1]+'.pddl'
    scenarios = workman.loadScenario(domain_file, task_file)
    print()

    # send to action by action to agent who needs to perform this action
    ###### create spatial representation of classic situation

    # search solution and send it to major agent
    solution = workman.search_solution()
    childpipe.send(solution)
    if name == major_agent:
        # receive solution and create an auction
        solutions = childpipe.recv()
        logging.info("Solutions received by major agent %s" % name)
        keeper = DecisionStrategies(solutions)
        # can be changed to any other strategy
        agents, solution = keeper.auction()
        # ask agents whose plan won to save their solutions, to other agents - save won agent solution (find in their plans the won plan).
        childpipe.send(solution)
    # Save solution
    solution_to_save = childpipe.recv()
    workman.save_solution(solution_to_save)



class Manager:
    def __init__(self, agents, problem, agpath = 'mapspatial.agent.agent_search', backward = False, subsearch = 'greedy'):
        self.agents = agents
        self.problem = problem
        self.agpath = agpath
        self.agtype = 'SpAgent'
        self.backward = backward
        self.subsearch = subsearch


    def manage_agents(self):

        allProcesses = []

        for ag in self.agents:
            parent_conn, child_conn = Pipe()
            p = Process(target=agent_activation,
                        args=(self.agpath, self.agtype,ag, self.agents, self.problem, self.backward, self.subsearch, child_conn, ))
            allProcesses.append((p, parent_conn))
            p.start()

        group_experience = []
        for pr, conn in allProcesses:
            group_experience.append((conn.recv(), conn))

        # Select the major (most experienced) agent
        most_exp = 0
        for info, _ in group_experience:
            if info[1] > most_exp:
                most_exp = info[1]

        major = [info[0] for info, conn in group_experience if info[1] == most_exp][0]

        # Major agent will create an auction and send back the best solution.
        for pr, conn in allProcesses:
            conn.send(major)

        solutions = {}
        # Receive solutions
        for info, conn in group_experience:
            solutions[info[0]] = conn.recv()

        # Send solutions to the major agent and receive final solution
        final_solution = None
        for info, conn in group_experience:
            if info[0] == major:
                conn.send(solutions)
                final_solution = conn.recv()
                break

        # Send final solution to all agents
        for info, conn in group_experience:
            conn.send(final_solution)

        for pr, conn in allProcesses:
            pr.join()




























