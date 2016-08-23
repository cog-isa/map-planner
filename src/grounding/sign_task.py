import datetime, os, pickle, logging
from .semnet import Sign, CausalMatrix

DEFAULT_FILE_PREFIX = 'wmodel_'
DEFAULT_FILE_SUFFIX = '.swm'


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
                    for pm in sign.meanings.copy():
                        if pm not in pms:
                            sign.remove_meaning(pm)
            # TODO (AP): check - not all deleted
            logging.info('\tSaving precedent...')
            self.start_situation.name += self.name
            dm = self.start_situation.meanings[0].copy_replace('meaning', 'image')
            self.start_situation.add_image(dm)

            self.start_situation.remove_meaning(self.start_situation.meanings[0])
            pm = CausalMatrix(self.start_situation)
            idx = 1
            for name, cm in plan:
                idx = pm.add_feature(cm, idx) + 1
            self.start_situation.add_meaning(pm)

            self.signs[self.start_situation.name] = self.start_situation
        else:
            for sign in self.signs:
                sign.meanings = []
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
