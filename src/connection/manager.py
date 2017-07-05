from grounding.agent_grounding import Agent
from multiprocessing import Pool
from connection.messagen import reconstructor


class Manager:

    def __init__(self, agents, problem, saveload):
        self.agents = agents
        self.problem = problem
        self.saveload = saveload
        self.solution = []

    # start server for every agent to communicate with each other and begin planning
    def agent_start(self, agent, port, others):
        agent.search_solution(port, others)
        # if not solution[1] is "solution":

        # return solution in queue or smthing else


    def search_solution(self):
        # binding a server socket for solution
        clagents = []
        port = 9098
        # socket = MySocket()
        # socket.bind('', port)
        # socket.listen()
        import socket
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.bind(('', port))
        serversocket.listen(5)
        new = 1
        for agent in self.agents:
            agent = Agent(agent, self.problem, self.saveload)
            port += new
            clagents.append([agent, port])
        for current_agent in clagents:
            others = [[agent[0].name, agent[1]] for agent in clagents if not agent is current_agent]
            current_agent.insert(2, others)

        pool = Pool(processes=len(clagents))
        multiple_results = [pool.apply_async(self.agent_start, (agent, port, others)) for agent, port, others in
                            clagents]

        while True:

            # print([res.get(timeout=1) for res in multiple_results])
            # print(len(multiple_results))

            (clientsocket, address) = serversocket.accept()
            # clientsocket.setblocking(0)
            solution = clientsocket.recv(1024)
            solution = solution.decode()

            if solution:
                print("solution on server! "+solution)
                self.solution.append(solution)
            else:
                print("No solution")
            print('connected:', address)
            if len(self.solution) == len(clagents):
                break
        clientsocket.close()
        self.solution = auction(self.solution)
        return self.solution

def auction(solutions):
    plans = {}
    auct = {}
    maxim = 1
    for sol in solutions:
        agent, plan = reconstructor(sol)
        plans[agent] = plan
    print(plans)
    for agent, plan in plans.items():
        if not plan in auct:
            auct[plan] = 1
        else:
            iter = auct[plan]
            auct[plan] = iter+1
            if iter+1 > maxim:
                maxim = iter+1
    print(auct)
    plan = [plan for plan, count in auct.items() if count==maxim][0]
    print(plan)
    return plan
















