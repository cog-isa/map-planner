import logging
import time

from mapplanner.grounding import pddl_grounding
from mapplanner.grounding import json_grounding
from mapplanner.search.mapsearch import MapSearch
from mapplanner.agent.messagen import Tmessage
from mapplanner.grounding.sign_task import Task


class Agent:
    def __init__(self):
        pass

    # Initialization
    def initialize(self, name, subjects, problem,logic, saveload, gazebo, LogicalSearch, ref):
        self.name = name
        self.subjects = subjects
        self.problem = problem
        self.is_load = saveload
        self.solution = []
        self.types = ['help_request', 'Approve', 'Broadcast']
        self.logic = logic
        self.gazebo = gazebo
        self.final_solution = ''
        self.LogicalSearch = LogicalSearch
        self.ref = ref

    # Grounding tasks
    # TODO approximate 2 grounding methods to 1
    def load_sw(self):
        logging.info('Grounding start: {0}'.format(self.problem.name))
        if self.is_load:
            signs = Task.load_signs(self.name)
            if self.logic == 'classic':
                task = pddl_grounding.ground(self.problem, self.name, self.subjects, self.logic, signs)
            elif self.logic == 'spatial':
                task = json_grounding.spatial_ground(self.problem, self.name, self.logic, signs)
        else:
            if self.logic == 'classic':
                task = pddl_grounding.ground(self.problem, self.name, self.subjects, self.logic)
            elif self.logic == 'spatial':
                task = json_grounding.spatial_ground(self.problem, self.name, self.logic)
        logging.info('Grounding end: {0}'.format(self.problem.name))
        logging.info('{0} Signs created'.format(len(task.signs)))
        return task

    def gazebo_visualization(self):
        print('This version of mapplanner does not support gazebo implementation. Use crumb_planner instead.')
        pass

    def search_solution(self, port, others):
        task = self.load_sw()
        logging.info('Search start: {0}, Start time: {1}'.format(task.name, time.clock()))
        connection_sign = task.signs["Send"]
        cms = connection_sign.spread_up_activity_motor('significance', 1)
        method = None
        cm = None
        for sign, action in cms:
            for connector in sign.out_significances:
                if connector.in_sign.name == "They" and len(others) > 1:
                    method = action
                    pm = connector.out_sign.significances[1]
                    cm = pm.copy('significance', 'meaning')
                elif connector.in_sign.name != "They" and len(others) == 1:
                    method = action
                    cm = connector.out_sign.significances[1].copy('significance', 'meaning')
                elif len(others) == 0:
                    method = 'save_achievement'
        search = MapSearch(task, self.LogicalSearch, self.ref, self.problem.task_file)
        solutions = search.search_plan()
        sol_acronims = []
        for sol in solutions:
            acronim = ''
            for act in sol:
                if act[3]:
                    if act[3].name == 'I':
                        name = self.name
                    else:
                        name = act[3].name
                else:
                    name = self.name
                acronim+= act[1] + ' '+name +';'
            sol_acronims.append(acronim)
        self.solution = search.long_relations(solutions)
        self.solution.append((connection_sign.add_meaning(), method, cm, task.signs["I"]))

        mes = Tmessage(self.solution, self.name)
        message = getattr(mes, method)()

        import socket
        #send sol to server
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.connect(('localhost', 9097))

        conn.send(message.encode("utf-8"))

        while True:
            auct_sol = conn.recv(1024)
            self.final_solution = auct_sol.decode()
            acr_to_save = ''
            if '&&' in self.final_solution:
                for acr in [a.split(';') for a in self.final_solution.split('&&')[:-1]]:
                    acr_to_save+=acr[0].strip() + ';'
            else:
                acr_to_save = ''
                for part in self.final_solution.split(';')[:-1:2]:
                    acr_to_save +=(part) + ';'

            if self.final_solution != '':
                print('Agent '+self.name+' got the final solution!')
                solution_to_save = []
                for acr in sol_acronims:
                    if acr_to_save[:-1] in acr:
                        solution_to_save.extend(solutions[sol_acronims.index(acr)])
                        break
                if not solution_to_save and solutions:
                    solution_to_save = solutions[0]
                break
        conn.close()

        if self.gazebo:
            self.gazebo_visualization()

        file_name = None
        if self.is_load:
            file_name = task.save_signs(solution_to_save)
            print(file_name)
        if file_name:
            logging.info('Agent ' + self.name + ' finished all works')

