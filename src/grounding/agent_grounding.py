import logging
from pddl.parser import Parser
from grounding import sign_grounding
from search.mapsearch import map_search
import time
from connection.messagen import Tmessage
import time

class Agent:
    def __init__(self, name, problem, saveload):
        self.name = name
        self.problem = problem
        self.is_load = saveload
        self.solution = []
        self.types = ['help_request', 'help_response', 'broadcast_message']


    def load_sw(self, problem, is_load):
        logging.info('Grounding start: {0}'.format(problem.name))
        task = sign_grounding.ground(problem, self.name)
        if is_load:
            task.load_signs()
        logging.info('Grounding end: {0}'.format(problem.name))
        logging.info('{0} Signs created'.format(len(task.signs)))
        return task


    def search_solution(self, port, others):
        task = self.load_sw(self.problem, self.is_load)
        search_start_time = time.clock()
        logging.info('Search start: {0}'.format(task.name))
        self.solution = map_search(task)
        mes = Tmessage(self.types[2], self.solution, self.name)
        message = mes.broadcast()

        #send sol to server
        import socket
        socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        socket.connect(('localhost', 9098))



        socket.send(message.encode())

        print("data have been send from client")

        if self.is_load:
            task.save_signs(self.solution)

        # return self.solution

