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
        for column in itertools.chain(self.left, self.right):
            for index, element in column:
                if element == sign:
                    return True

        return False

    def __gt__(self, smaller):
        # TODO: not all variants and right part
        included = []
        for s_column in smaller.left:
            for j, b_column in enumerate(self.left):
                if j not in included and s_column < b_column:
                    included.append(j)
                    break
            else:
                return False
        return True

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
        return len(self.left) == 0 and len(self.right) == 0

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

    def __contains__(self, item):
        return any([item in img for img in self.images])

    def is_action(self):
        return any([len(fragment.right) > 0 for fragment in self.images])

    def get_parents(self):
        parents = frozenset()
        for s in self.significance:
            for index, val in s.get_components():
                if not val.is_action():
                    parents |= {val}
        return parents

    def get_children(self):
        children = frozenset()
        for image in self.images:
            for index, val in image.get_components():
                second_level = val.get_children()
                if len(second_level) > 0:
                    children |= second_level
                else:
                    children |= {(index, val)}
        return children

    def has_parent(self, parent):
        if any([parent in s for s in self.significance]):
            return True
        else:
            for s in self.significance:
                if any([component.has_parent(parent) for index, component in s.get_components()]):
                    return True
            return False


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
