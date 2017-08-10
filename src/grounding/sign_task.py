import datetime
import logging
import os
import pickle
import itertools

from .semnet import Sign

DEFAULT_FILE_PREFIX = 'wmodel_'
DEFAULT_FILE_SUFFIX = '.swm'

SIT_COUNTER = 0
SIT_PREFIX = 'situation_'
PLAN_PREFIX = 'action_'


class Task:
    def __init__(self, name, signs, start_situation, goal_situation):
        self.name = name
        self.signs = signs
        self.start_situation = start_situation
        self.goal_situation = goal_situation

    def __str__(self):
        s = 'Task {0}\n  Signs:  {1}\n  Start:  {2}\n  Goal: {3}\n'
        return s.format(self.name, '\n'.join(map(repr, self.signs)),
                        self.start_situation, self.goal_situation)

    def __repr__(self):
        return '<Task {0}, signs: {1}>'.format(self.name, len(self.signs))

    def save_signs(self, plan):
        I_obj = None
        logging.info('Plan preparation to save...')
        if plan:
            logging.info('\tCleaning SWM...')
            pms = [pm for _, _,pm, _ in plan]
            for name, s in self.signs.copy().items():
                signif=list(s.significances.items())
                if name.startswith(SIT_PREFIX):
                    for index, pm in s.meanings.copy().items():
                        if pm not in pms:
                            s.remove_meaning(pm) # delete all situations
                    self.signs.pop(name)
                elif len(signif):
                    if len(signif[0][1].cause) and len(signif[0][1].effect): #delete action's meanings that are not in plan
                        for index, pm in s.meanings.copy().items():
                            pm_signs = pm.get_signs()
                            for pm_sign in pm_signs:
                                if "?" in pm_sign.name: # delete only fully signed actions
                                    break
                            else:
                                if pm not in pms:
                                    s.remove_meaning(pm)



            They_signs = [con.in_sign for con in self.signs["They"].out_significances]
            I_obj = [con.in_sign for con in self.signs["I"].out_significances if con.out_sign.name == "I"]

            for agent in itertools.chain(They_signs, I_obj):
                for connector in list(agent.out_meanings.copy()):
                    pm = connector.in_sign.meanings[connector.in_index]
                    if pm not in pms:
                        pm_signs = pm.get_signs()
                        for pm_sign in pm_signs:
                            if "?" in pm_sign.name:  # delete only fully signed actions
                                break
                        else:
                            agent.out_meanings.remove(connector)



            logging.info('\tSaving precedent...')
            self.start_situation.name += self.name
            self.goal_situation.name += self.name
            dm = self.start_situation.meanings[1].copy('meaning', 'image')
            self.start_situation.add_image(dm)
            dm = self.goal_situation.meanings[1].copy('meaning', 'image')
            self.goal_situation.add_image(dm)
            # in start and goal sit out_meanings insert connector to plan sign
            plan_sign = Sign(PLAN_PREFIX + self.name)
            plan_mean = plan_sign.add_meaning()
            connector = plan_mean.add_feature(self.start_situation.meanings[1])
            self.start_situation.add_out_meaning(connector)
            conn = plan_mean.add_feature(self.goal_situation.meanings[1], effect=True)
            self.goal_situation.add_out_meaning(conn)


            plan_image = plan_sign.add_image()

            for _, name, cm, agent in plan:
                im = cm.sign.add_image()
                connector = plan_image.add_feature(im)
                cm.sign.add_out_image(connector) # add connector to plan_sign threw images to out_image


            self.signs[plan_sign.name] = plan_sign
            self.signs[self.start_situation.name] = self.start_situation
            self.signs[self.goal_situation.name] = self.goal_situation
        else:
            for name, sign in self.signs.copy().items():
                if name.startswith(SIT_PREFIX):
                    self.signs.pop(name)
                else:
                    sign.meanings = {}
                    sign.out_meanings = []
        if I_obj:
            I_obj = "_"+I_obj[0].name
        file_name = DEFAULT_FILE_PREFIX + datetime.datetime.now().strftime('%d_%H_%M') + I_obj + DEFAULT_FILE_SUFFIX
        logging.info('Start saving to {0}'.format(file_name))
        logging.info('\tDumping SWM...')
        pickle.dump(self.signs, open(file_name, 'wb'))
        return file_name

    @staticmethod
    def load_signs(agent, file_name=None):
        signs = []
        if not file_name:
            for f in os.listdir('.'):
                if f.endswith(DEFAULT_FILE_SUFFIX) and f.split(".")[0].endswith(agent):
                    file_name = f
                    break
            else:
                logging.info('File not found')
                return None
        if file_name:
            signs = pickle.load(open(file_name, 'rb'))
        return signs
