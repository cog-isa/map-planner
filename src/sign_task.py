import itertools


class SignImage:
    def __init__(self, conditions, sign=None, effects=None):
        self.conditions = conditions
        self.sign = sign
        if not effects:
            self.effects = []
        else:
            self.effects = effects

    def __str__(self):
        return '{0}->{1}'.format(self.conditions, self.effects)

    def __repr__(self):
        return '<SignImage {0}->{1}>'.format(self.conditions, self.effects)

    def __eq__(self, other):
        if not len(self.conditions) == len(other.conditions) or not len(self.effects) == len(other.effects):
            return False
        return all([cond1 == cond2 for cond1, cond2 in zip(self.conditions, other.conditions)]) and all(
            [eff1 == eff2 for eff1, eff2 in zip(self.effects, other.effects)])

    def __hash__(self):
        return 3 * hash(tuple([frozenset(s) for s in self.conditions])) \
               + 5 * hash(tuple([frozenset(s) for s in self.effects]))

    def update(self, column, sign, condition):
        part = self.conditions if condition else self.effects

        if len(part) <= column:
            for _ in range(column - len(part) + 1):
                part.append(set())
        if sign not in part[column]:
            part[column].add(sign)

    def replace(self, old_comp, new_comp):
        for i in range(len(self.conditions)):
            new_cond = set()
            for val in self.conditions[i]:
                if val.is_action():
                    image = val.image[0].copy()
                    image.replace(old_comp, new_comp)
                    val.meaning.append(image)
                    new_cond.add()
                elif val == old_comp:
                    new_cond.add(new_comp)
                else:
                    new_cond.add(val)
            self.conditions[i] = new_cond
        for i in range(len(self.effects)):
            new_cond = set()
            for val in self.effects[i]:
                if val.is_action():
                    new_sign = val.copy()
                    for image in new_sign.images:
                        image.replace(old_comp, new_comp)
                    new_cond.add(new_sign)
                elif val == old_comp:
                    new_cond.add(new_comp)
                else:
                    new_cond.add(val)
            self.effects[i] = new_cond

    def is_absorbing(self, sign):
        if any([sign in column for column in self.conditions]):
            return True
        if any([sign in column for column in self.effects]):
            return True

        return False

    def get_components(self):
        result = frozenset()
        for column in itertools.chain(self.conditions, self.effects):
            result |= column
        return result

    def get_conditions(self):
        result = frozenset()
        for column in self.conditions:
            result |= column
        return result

    def get_effects(self):
        result = frozenset()
        for column in self.effects:
            result |= column
        return result

    def copy(self):
        cond, eff = [], []
        for c in self.conditions:
            cond.append(c.copy())
        for e in self.effects:
            eff.append(e.copy())
        return SignImage(cond, effects=eff)


class Sign:
    """
        Sign - element of model of the world

        name - an unique string
        significance - a set of signs
        image - a list of SignImages
        meaning - a dict of SignImages
    """
    def __init__(self, name, significance=None, meaning=None, image=None):
        self.name = name
        self.significance = significance
        if not significance:
            self.significance = set()
        else:
            self.significance = significance

        self.images = []
        if image:
            self.images.append(image)
            image.sign = self

        if not meaning:
            self.meaning = {}
        else:
            self.meaning = meaning

    def __str__(self):
        s = 'Sign {0}:\n    p={1}\n   m={2}\n   a={3}'
        return s.format(self.name, self.images, self.significance, self.meaning)

    def __repr__(self):
        return '<Sign {0}>'.format(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def update_image(self, column, sign, condition=True, index=0):
        if len(self.images) <= index:
            sign_image = SignImage([], sign=self)
            self.images.append(sign_image)
        self.images[index].update(column, sign, condition)

    def is_action(self):
        return any([len(image.effects) > 0 for image in self.images])

    def get_parents(self):
        parents = set()
        for val in self.significance:
            if not val.is_action():
                parents.add(val)
        return parents

    def is_absorbing(self, sign):
        return any([img.is_absorbing(sign) for img in self.images])


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
