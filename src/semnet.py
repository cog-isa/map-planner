import itertools


class PredictionMatrix:
    """
    Prediction matrix - main structure in semiotic network defined causal and hierarchical relations
    cause - is the list of causal events at each moment
    cause - is the list of effect events at each moment (can be empty)
    """

    def __init__(self, cause, sign, uid, effect=None):
        self.cause = cause
        self.sign = sign
        self.uid = uid
        if not effect:
            self.effect = []
        else:
            self.effect = effect

    def __str__(self):
        return '[{0}]->[{1}]'.format(','.join(self.cause), ','.join(self.effect))

    def __repr__(self):
        return '<PredictionMatrix {0}:{1} [{2}]->[{3}]>'.format(self.sign, self.uid, ','.join(self.cause),
                                                                ','.join(self.effect))

    def __eq__(self, other):
        return self.sign == other.sign and self.uid == other.id

    def __hash__(self):
        return hash(self.uid) + hash(self.sign)

    def __contains__(self, sign):
        for event in itertools.chain(self.cause, self.effect):
            if sign in event:
                return True

        return False

    def __gt__(self, smaller):
        for event in smaller.cause:
            if event not in self.cause:
                return False

        for event in smaller.effect:
            if event not in self.effect:
                return False

        return True

    def deep_equals(self, other):
        if not len(self.cause) == len(other.cause) or not len(self.effect) == len(other.effect):
            return False
        return all([event1 == event2 for event1, event2 in zip(self.cause, other.cause)]) and all(
            [event1 == event2 for event1, event2 in zip(self.effect, other.effect)])

    def add_feature(self, feature, effect=False, index=None):
        part = self.cause if effect else self.effect

        if index is None or index >= len(part):
            index = len(part)
            part.append(Event(index, [feature]))
        elif len(part) < index:
            part[index].add(feature)

    def is_empty(self):
        return len(self.cause) == 0 and len(self.effect) == 0

    def copy(self):
        cause, effect = [], []
        for c in self.cause:
            cause.append(c.copy())
        for e in self.effect:
            effect.append(e.copy())
        return PredictionMatrix(cause, None, None, effect)

    def get_signs(self):
        signs = set()
        for event in itertools.chain(self.cause, self.effect):
            signs |= event.get_signs()


class Event:
    """
    Event - the set of coincident prediction matrices
    """

    def __init__(self, index, coincidences=None):
        self.index = index
        if not coincidences:
            self.coincidences = set()

    def __str__(self):
        return '{{0}}'.format(','.join(self.coincidences))

    def __repr__(self):
        return '<Event {0}: {{1}}>'.format(self.index, ','.join([x.sign for x in self.coincidences]))

    def __eq__(self, other):
        return self.coincidences == other.coincidences

    def __contains__(self, sign):
        for pm in self.coincidences:
            if pm.sign == sign:
                return True

        return False

    def get_signs(self):
        return [pm.sign for pm in self.coincidences]

    def copy(self):
        return Event(self.index, self.coincidences.copy())


class Sign:
    """
        Sign - element of model of the world

        name - an unique string
        significances - a list of parent's PredictionMatrices with indexes
        images - a list of PredictionMatrices
        meanings - a list of parent's PredictionMatrices with indexes
    """

    def __init__(self, name, image=None, significance=None, meaning=None):
        self.name = name
        if image:
            self.images = [image]
        else:
            self.images = []

        if significance:
            self.significances = [significance]
        else:
            self.significances = []

        if meaning:
            self.meanings = [meaning]
        else:
            self.meanings = []

    def __str__(self):
        return '"{0}"'.format(self.name)

    def __repr__(self):
        return '<Sign "{0}":\n\tp={1},\n\tm={2},\n\ta={3}>'.format(self.name, self.images, self.significances,
                                                                   self.meanings)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def add_image(self, pm):
        pm.sign = self
        pm.uid = len(self.images)
        self.images.append(pm)

    def add_significance(self, pm, index):
        self.significances.append((pm, index))

    def add_meaning(self, pm, index):
        self.meanings.append((pm, index))

    def is_action(self):
        return any([len(matrix.effect) > 0 for matrix in self.images])

    def get_classes(self):
        return set([pm.sign for pm, _ in self.significances if not pm.sign.is_action()])

    def get_components(self):
        components = set()
        for pm in self.images:
            components |= pm.get_signs()
        return components
