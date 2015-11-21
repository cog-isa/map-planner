__author__ = 'Aleksandr'


class Sign:
    def __init__(self, name, significance=None, meaning=None, image=None):
        self.name = name
        self.significance = significance
        self.meaning = meaning
        if not image:
            self.image = ([],[])
        else:
            self.image = image

    def __str__(self):
        s = 'Sign {0}:\n    p=[{1}]\n   m=[{2}]\n   a=[{3}]'
        return s.format(self.name, self.image, self.significance, self.meaning)

    def __repr__(self):
        return '<Sign {0}>'.format(self.name)

    def update_image(self, i, sign, condition=True):
        index = 0 if condition else 1

        if len(self.image[index]) <= i:
            for _ in range(i - len(self.image[index]) + 1):
                self.image[index].append(set())
        if sign not in self.image[index][i]:
            self.image[index][i].update([sign])


class Task:
    def __init__(self, name, signs, start_situation, goal_situation):
        self.name = name
        self.signs = signs
        self.start_situation = start_situation
        self.goal_situation = goal_situation

    def __str__(self):
        s = 'Task {0}\n  Signs:  {1}\n  Start:  {2}\n  Goal: {3}\n'
        return s.format(self.name, ', '.join(map(repr, self.signs)),
                        self.start_situation, self.goal_situation)

    def __repr__(self):
        return '<Task {0}, signs: {1}>'.format(self.name, len(self.signs))
