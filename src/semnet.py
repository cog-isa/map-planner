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
        self.out_links = []
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
        return self.sign == other.sign and self.uid == other.uid

    def __hash__(self):
        return hash(self.uid) + hash(self.sign)

    def __contains__(self, pm):
        for event in itertools.chain(self.cause, self.effect):
            if pm in event:
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

    def add_feature(self, feature, seq=None, effect=False):
        mult, part = (-1, self.effect) if effect else (1, self.cause)

        if seq is None:
            seq = len(part)
            index = (len(part) + 1) * mult
            part.append(Event(index, {feature}))
        else:
            part[seq].coincidences.add(feature)
            index = (seq + 1) * mult
        feature.add_out_link(self, index)
        return seq

    def add_out_link(self, pm, index):
        for lpm, indexes in self.out_links:
            if lpm == pm:
                indexes.append(index)
                break
        else:
            self.out_links.append((pm, [index]))

    def is_empty(self):
        return len(self.cause) == 0 and len(self.effect) == 0

    def copy(self):
        cause, effect = [], []
        for c in self.cause:
            cause.append(c.copy())
        for e in self.effect:
            effect.append(e.copy())
        return PredictionMatrix(self.sign, None, cause, effect)

    def deep_copy(self):
        cause, effect = [], []
        for c in self.cause:
            cause.append(c.deep_copy())
        for e in self.effect:
            effect.append(e.deep_copy())
        return PredictionMatrix(self.sign, self.uid, cause, effect)

    def get_signs(self):
        signs = set()
        for event in itertools.chain(self.cause, self.effect):
            signs |= event.get_signs()
        return signs

    def replace(self, old_pm, new_pm):
        for event in itertools.chain(self.cause, self.effect):
            event.replace(old_pm, new_pm)


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

    def __contains__(self, pm):
        return pm in self.coincidences

    def get_signs(self):
        return {pm.sign for pm in self.coincidences}

    def copy(self):
        return Event(self.index, self.coincidences.copy())

    def deep_copy(self):
        return Event(self.index, {pm.deep_copy() for pm in self.coincidences})

    def replace(self, old_pm, new_pm):
        for pm in self.coincidences.copy():
            if pm == old_pm:
                self.coincidences.remove(old_pm)
                self.coincidences.add(new_pm)
            else:
                pm.replace(old_pm, new_pm)


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

    def get_new_image(self):
        pm = PredictionMatrix(self, len(self.images))
        self.images.append(pm)
        return pm

    def get_new_significance(self):
        pm = PredictionMatrix(self, len(self.significances))
        self.significances.append(pm)
        return pm

    def get_new_meaning(self):
        pm = PredictionMatrix(self, len(self.meanings))
        self.meanings.append(pm)
        return pm

    def is_action(self):
        return any([len(matrix.effect) > 0 for matrix in self.images]) or any(
            [len(matrix.effect) > 0 for matrix in self.significances])

    def is_abstract(self):
        return len(self.images) == 0

    def get_parents(self):
        return set([pm.sign for pm, _ in self.significances if not pm.sign.is_action()])

    def get_components(self):
        components = set()
        for pm in self.images:
            components |= pm.get_signs()
        return components

    def get_own_scripts(self):
        scripts = []
        for significance in self.significances:
            for pm, index in significance.out_links:
                if pm.sign.is_action():
                    scripts.append(pm.copy())
        return scripts

    def get_inherited_scripts(self):
        scripts = []
        for significance in self.significances:
            for pm, index in significance.out_links:
                # we want to replace abstract signs and not relations
                if not pm.sign.is_action() and len(pm.get_signs()) == 1:
                    inherited = pm.sign.get_own_scripts() + pm.sign.get_inherited_scripts()
                    for inh in inherited:
                        replaced = inh.deep_copy()
                        replaced.replace(pm, significance)
                        scripts.append(replaced)
        return scripts
