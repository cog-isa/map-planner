import logging
from grounding import sign_grounding
from search.mapsearch import map_search
from connection.messagen import Tmessage
import time
from .sign_task import Task

class Agent:
    def __init__(self, name, subjects, problem, saveload):
        self.name = name
        self.subjects = subjects
        self.problem = problem
        self.is_load = saveload
        self.solution = []
        self.types = ['help_request', 'Approve', 'Broadcast']


    def load_sw(self, problem, is_load):
        logging.info('Grounding start: {0}'.format(problem.name))
        if is_load:
            signs = Task.load_signs(self.name)
            task = sign_grounding.ground(problem, self.name, self.subjects, signs)
        else:
            task = sign_grounding.ground(problem, self.name, self.subjects)
        logging.info('Grounding end: {0}'.format(problem.name))
        logging.info('{0} Signs created'.format(len(task.signs)))
        return task


    def search_solution(self, port, others):
        task = self.load_sw(self.problem, self.is_load)
        search_start_time = time.clock()
        logging.info('Search start: {0}'.format(task.name))

        sit_sign = task.signs["Send"]
        cms = sit_sign.spread_up_activity_motor('significance', 1)
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

        self.solution = map_search(task)

        self.solution.append((sit_sign.add_meaning(), method, cm, task.signs["I"]))

        mes = Tmessage(self.solution, self.name)
        message = getattr(mes, method)()

        #send sol to server
        import socket
        socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.connect(('localhost', 9097))

        if self.is_load:
            task.save_signs(self.solution)

        socket.send(message.encode())



        # return self.solution

