import itertools


class NetworkFragment:
    """
        NetworkFragment - part of sign components

        left - list of sets of pairs (index, sign)
        left - delayed list of sets of pairs (index, sign)
    """

    def __init__(self, left, right=None):
        self.left = left
        if not right:
            self.right = []
        else:
            self.right = right

    def __str__(self):
        return '{0}->{1}'.format(self.left, self.right)

    def __repr__(self):
        return '<NetworkFragment {0}->{1}>'.format(self.left, self.right)

    def __eq__(self, other):
        if not len(self.left) == len(other.left) or not len(self.right) == len(other.right):
            return False
        return all([column1 == column2 for column1, column2 in zip(self.left, other.left)]) and all(
            [column1 == column2 for column1, column2 in zip(self.right, other.right)])

    def __hash__(self):
        return 3 * hash(tuple([frozenset(s) for s in self.left])) \
               + 5 * hash(tuple([frozenset(s) for s in self.right]))

    def __contains__(self, sign):
        if any([sign in [pair[1] for pair in column] for column in self.left]):
            return True
        if any([sign in [pair[1] for pair in column] for column in self.right]):
            return True

        return False

    def add(self, pair, not_delay=True, column_index=None):
        part = self.left if not_delay else self.right

        if column_index is None:
            column_index = len(part)
            part.append(set())
        elif len(part) <= column_index:
            for _ in range(column_index - len(part) + 1):
                part.append(set())
        if pair not in part[column_index]:
            part[column_index].add(pair)

    def is_empty(self):
        return len(self.left) == 0 or len(self.right) == 0

    def replace(self, old_comp, new_comp):
        for i in range(len(self.left)):
            new_cond = set()
            for val in self.right[i]:
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

    def get_components(self):
        result = frozenset()
        for column in itertools.chain(self.left, self.right):
            result |= column
        return result

    def get_left(self):
        result = frozenset()
        for column in self.left:
            result |= column
        return result

    def get_right(self):
        result = frozenset()
        for column in self.right:
            result |= column
        return result

    def copy(self):
        left, right = [], []
        for c in self.left:
            left.append(c.copy())
        for e in self.right:
            right.append(e.copy())
        return NetworkFragment(left, right=right)


class Sign:
    """
        Sign - element of model of the world

        name - an unique string
        significance - a list of NetworkFragments
        image - a list of NetworkFragments
        meaning - a list of NetworkFragments
    """

    def __init__(self, name, image=None, significance=None, meaning=None):
        self.name = name
        if significance:
            self.significance = significance
        else:
            self.significance = [NetworkFragment([])]

        if image:
            self.images = [image]
        else:
            self.images = [NetworkFragment([])]

        if meaning:
            self.meaning = meaning
        else:
            self.meaning = []

    def __str__(self):
        s = 'Sign {0}:\n    p={1}\n   m={2}\n   a={3}'
        return s.format(self.name, self.images, self.significance, self.meaning)

    def __repr__(self):
        return '<Sign {0}>'.format(self.name)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def is_action(self):
        return any([len(fragment.right) > 0 for fragment in self.images])

    def get_parents(self):
        parents = frozenset()
        for val in self.significance:
            if not val.is_action():
                parents |= {val}
        return parents

    def __contains__(self, item):
        return any([item in img for img in self.images])


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
