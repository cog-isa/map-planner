import datetime, os, pickle
from .semnet import Sign

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

    def save_signs(self):
        file_name = DEFAULT_FILE_PREFIX + datetime.datetime.now().strftime('%y_%m_%d_%H_%M_%S') + DEFAULT_FILE_SUFFIX
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
