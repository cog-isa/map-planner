import json
import logging
import pickle
import random
import re

types = ['help_request', 'Approve', 'Broadcast']

greetings = ['Hello ', 'Greetings ', 'Good day ']
questions = ['Can you help to achieve the goal?', 'What can you do in this situation?']
sit = ['The situation is', 'Now, we have']

templates = {}

templates["handempty"] = "agent ?ag has an empty manipulator"
templates["on"] = "block ?x on block ?y"
templates["blocktype"] = "block ?size ?x"
templates["ontable"] = "block ?x is on the table"
templates["clear"] = "block ?x is clear"
templates["holding"] = "agent ?ag holding block ?x"


class Tmessage:
    def __init__(self, plan, agents, active_pm=None, checked_pm=None):
        # for agents which can make multiple actions with different type of block. Not to remake previous actions.
        self.actions = plan
        self.agents = agents
        self.hagent = None
        self.bagents = None
        self.active_pm = active_pm
        self.checked_pm = checked_pm
        self.lagents = set()
        self.lsizes = set()
        self.lblocks = set()

    def xstr(self, sit):
        if sit is None:
            return ""
        else:
            return sit.name

    def broadcast(self):
        message=random.choice(greetings)+"all!!! My name is " +self.agents+  ". I have made a plan and it is: "
        if self.actions and not self.bagents:
            for situation in self.actions:
                message+= situation[1] + " "+ self.xstr(situation[3])+ "; "
            return message
        elif self.bagents:
            return "broadcast to special agents"
        else:
            return "plan doesn't exist"

    # get grounded predicates from situation
    def get_sit_predicate(self, sit):
        predicates = []

        events=list(sit.sign.meanings.items())[0][1].cause
        for event in events:
            pred = []
            if len(event.coincidences)> 1:
                for con in event.coincidences:
                    pred.append(con.out_sign.name)
                    for connector in con.out_sign.out_significances:
                        if connector.in_sign.name == "size":
                            self.lsizes.add(connector.out_sign.name)
                        elif connector.in_sign.name == "agent":
                            self.lagents.add(connector.out_sign.name)
                        elif connector.in_sign.name == "block":
                            self.lblocks.add(connector.out_sign.name)
                predicates.append(pred)
            else:
                for connector in event.coincidences:
                    if connector.out_index > 0:
                        # connector.out_sign with index
                        pm = connector.get_out_cm('meaning')
                        cms = pm.spread_down_activity('meaning', 1)
                        predicates.append([cms[0][0].sign.name, cms[0][1].sign.name, cms[1][1].sign.name])

        return predicates

    # make phrase from templates and predicates
    def make_phrase(self, sit_predicates):
        phrase = ""
        lphrase = []
        for pred in sit_predicates:
            for item in pred:
                if item in templates:
                    message = templates[item]
                    for link in [item2 for item2 in pred if not item2 == item]:
                        if link in self.lagents:
                            message = re.sub("\?ag", link, message)
                        elif link in self.lblocks:
                            if "?x" in message:
                                message = re.sub("\?x", link, message)
                            elif "?y" in message:
                                message = re.sub("\?y", link, message)
                        elif link in self.lsizes:
                            message = re.sub("\?size", link, message)
                    lphrase.append(message)
        for item in lphrase[:-1]:
            phrase = phrase + item + ", "
        phrase = phrase + lphrase[len(lphrase)-1] + "."
        return phrase
    #for situation grounding
    def active_pm_reader(self):
        predicates = self.get_sit_predicate(self.active_pm)
        message = self.make_phrase(predicates)
        return message

    def approve(self):
        if isinstance(self.agents, list):
            self.bagents = self.agents
        elif isinstance(self.agents, str):
            self.hagent = self.agents
        else:
            logging.info("wrong amount of agents!")
        if self.bagents:
            self.broadcast()
        message=random.choice(greetings)+"all!!! My name is " +self.agents+  ". I have made a plan and it is: "
        if self.actions:
            for situation in self.actions:
                message+= situation[1] + " "+ self.xstr(situation[3])+ "; "
            return message
        else:
            return "plan doesn't exist"
    def save_achievement(self):
        message = random.choice(greetings) + "My name is " + self.agents + ". I have made a plan and it is: "
        if self.actions:
            for situation in self.actions:
                message+= situation[1] + " "+ self.xstr(situation[3])+ "; "
            with open('data.pickle', 'wb') as f:
                pickle.dump(message, f)
            return message
        else:
            return "plan doesn't exist"

def reconstructor(message):
    m = re.search('(?<=My name is )\w+', message)
    agent = m.group(0)
    plan = message.split(":")[1]
    plan = re.sub("I", agent, plan)
    return agent, plan