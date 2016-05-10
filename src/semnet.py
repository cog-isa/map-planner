import itertools


class PredictionMatrix:
    """
    Prediction matrix - main structure in semiotic network defined causal and hierarchical relations
    cause - is the list of causal events at each moment
    cause - is the list of effect events at each moment (can be empty)
    """

    def __init__(self, sign, uid, cause=None, effect=None):
        self.sign = sign
        self.uid = uid
        if not cause:
            self.cause = []
        else:
            self.cause = cause
        if not effect:
            self.effect = []
        else:
            self.effect = effect

    def __str__(self):
        return '[{0}]->[{1}]'.format(','.join(map(str, self.cause)), ','.join(map(str, self.effect)))

    def __repr__(self):
        return '<PredictionMatrix {0}:{1} [{2}]->[{3}]>'.format(self.sign.name, self.uid,
                                                                ','.join(map(repr, self.cause)),
                                                                ','.join(map(repr, self.effect)))

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

    def add_feature(self, feature, index=None, effect=False):
        """
        feature: PredictionMatrix of existed sign
        """
        part = self.effect if effect else self.cause

        if index is None or index >= len(part):
            index = len(part)
            part.append(Event(index, {feature}))
        elif len(part) < index:
            part[index].add(feature)
        return index

    def is_empty(self):
        return len(self.cause) == 0 and len(self.effect) == 0

    def copy(self):
        cause, effect = [], []
        for c in self.cause:
            cause.append(c.copy())
        for e in self.effect:
            effect.append(e.copy())
        return PredictionMatrix(None, None, cause, effect)

    def get_signs(self):
        signs = set()
        for event in itertools.chain(self.cause, self.effect):
            signs |= event.get_signs()

    def get_index(self, sign):
        index = 0
        for event in itertools.chain(self.cause, self.effect):
            if sign in event.get_signs():
                return index
            index += 1


class Event:
    """
    Event - the set of coincident prediction matrices
    """

    def __init__(self, index, coincidences=None):
        self.index = index
        if not coincidences:
            self.coincidences = set()
        else:
            self.coincidences = coincidences

    def __str__(self):
        return '{{{0}}}'.format(','.join(str(x.sign) for x in self.coincidences))

    def __repr__(self):
        return '<Event {0}: {{{1}}}>'.format(self.index, ','.join(x.sign.name for x in self.coincidences))

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
            self.images = [PredictionMatrix(self, 0)]

        if significance:
            self.significances = [significance]
        else:
            self.significances = [PredictionMatrix(self, 0)]

        if meaning:
            self.meanings = [meaning]
        else:
            self.meanings = [PredictionMatrix(self, 0)]

    def __str__(self):
        return '"{0}"'.format(self.name)

    def __repr__(self):
        return '<Sign "{0}":\n\tp={1},\n\tm={2},\n\ta={3}>'.format(self.name, self.images, self.significances,
                                                                   self.meanings)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def get_new_significance(self):
        if not self.significances[-1].is_empty():
            self.significances.append(PredictionMatrix(self, len(self.significances)))
        return self.significances[-1]

    def get_new_meaning(self):
        if not self.meanings[-1].is_empty():
            self.meanings.append(PredictionMatrix(self, len(self.meanings)))
        return self.meanings[-1]

    def is_action(self):
        return any([len(matrix.effect) > 0 for matrix in self.images])

    def get_parents(self):
        return set([pm.sign for pm, _ in self.significances if not pm.sign.is_action()])

    def get_components(self):
        components = set()
        for pm in self.images:
            components |= pm.get_signs()
        return components
