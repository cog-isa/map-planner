import datetime
import logging
import os
import pickle

from .semnet import Sign

DEFAULT_FILE_PREFIX = 'wmodel_'
DEFAULT_FILE_SUFFIX = '.swm'

SIT_COUNTER = 0
SIT_PREFIX = 'situation_'
PLAN_PREFIX = 'plan_'


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
        file_name = DEFAULT_FILE_PREFIX + datetime.datetime.now().strftime('%y_%m_%d_%H_%M_%S') + DEFAULT_FILE_SUFFIX
        logging.info('Start saving to {0}'.format(file_name))
        if plan:
            logging.info('\tCleaning SWM...')
            pms = [pm for _, pm in plan]
            for name, sign in self.signs.items():
                if not sign.out_meanings:
                    for index, pm in sign.meanings.copy().items():
                        if pm not in pms:
                            sign.remove_meaning(pm)
            for name, s in self.signs.copy().items():
                if name.startswith(SIT_PREFIX):
                    for index, pm in s.meanings.copy().items():
                        if pm not in pms:
                            s.remove_meaning(pm)
                    self.signs.pop(name)

            logging.info('\tSaving precedent...')
            self.start_situation.name += self.name
            self.goal_situation.name += self.name
            dm = self.start_situation.meanings[1].copy('meaning', 'image')
            self.start_situation.add_image(dm)
            dm = self.goal_situation.meanings[1].copy('meaning', 'image')
            self.goal_situation.add_image(dm)

            plan_sign = Sign(PLAN_PREFIX + self.name)
            plan_mean = plan_sign.add_meaning()
            connector = plan_mean.add_feature(self.start_situation.meanings[1])
            self.start_situation.add_out_meaning(connector)
            conn = plan_mean.add_feature(self.goal_situation.meanings[1], effect=True)
            self.goal_situation.add_out_meaning(conn)

            plan_image = plan_sign.add_image()
            effect = False
            for name, cm in plan:
                # TODO: add actual triplet of components for all signs to access to the current image
                im = cm.sign.add_image()
                connector = plan_image.add_feature(im, effect=effect)
                cm.sign.add_out_image(connector)
                effect = True

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
        logging.info('\tDumping SWM...')
        pickle.dump(self.signs, open(file_name, 'wb'))
        return file_name

    def load_signs(self, file_name=None):
        if not file_name:
            for f in os.listdir('.'):
                if f.endswith(DEFAULT_FILE_SUFFIX):
                    file_name = f
                    break
            else:
                raise Exception('File not found')
        self.signs = pickle.load(open(file_name, 'rb'))
        return file_name
