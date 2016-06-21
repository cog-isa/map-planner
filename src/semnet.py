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
        return self.sign == other.sign and self.uid == other.uid

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

    def add_feature(self, feature, seq=None, effect=False):
        """

        @param feature: pair of sign and index, index =0 is special case for "all connection"
        @param seq: predefined index to insert (starts from 1)
        @param effect: if it's effect part
        @return: resulted index inserted
        """
        mult, part = (-1, self.effect) if effect else (1, self.cause)

        if seq is None:
            index = (len(part) + 1) * mult
            part.append(Event(index, {feature}))
        else:
            part[abs(seq) - 1].coincidences.add(feature)
            index = abs(seq) * mult
        return index

    def is_empty(self):
        return len(self.cause) == 0 and len(self.effect) == 0


class Event:
    """
    Event - the set of coincident pairs (sign, index)
    """

    def __init__(self, index, coincidences=None):
        self.index = index
        if not coincidences:
            self.coincidences = set()
        else:
            self.coincidences = coincidences

    def __str__(self):
        return '{{{0}}}'.format(','.join(str(x) for x in self.coincidences))

    def __repr__(self):
        return '<Event {0}: {{{1}}}>'.format(self.index,
                                             ','.join('{0}:{1}'.format(x.name, conn) for x, conn in self.coincidences))

    def __eq__(self, other):
        return self.coincidences == other.coincidences

    def __contains__(self, sign):
        return sign in self.coincidences


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
        self.out_significances = []
        self.out_images = []
        self.out_meanings = []

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
        return pm, len(self.images)

    def get_new_significance(self):
        pm = PredictionMatrix(self, len(self.significances))
        self.significances.append(pm)
        return pm, len(self.significances)

    def get_new_meaning(self):
        pm = PredictionMatrix(self, len(self.meanings))
        self.meanings.append(pm)
        return pm, len(self.meanings)

    def add_out_significance(self, pm, index):
        for lpm, indexes in self.out_significances:
            if lpm == pm:
                indexes.append(index)
                break
        else:
            self.out_significances.append((pm, [index]))

    def add_out_image(self, pm, index):
        for lpm, indexes in self.out_images:
            if lpm == pm:
                indexes.append(index)
                break
        else:
            self.out_images.append((pm, [index]))

    def add_out_meaning(self, pm, index):
        for lpm, indexes in self.out_meanings:
            if lpm == pm:
                indexes.append(index)
                break
        else:
            self.out_meanings.append((pm, [index]))

    def is_action(self):
        return any([len(matrix.effect) > 0 for matrix in self.images]) or any(
            [len(matrix.effect) > 0 for matrix in self.significances])

    def is_abstract(self):
        return len(self.images) == 0

    def get_parents(self):
        return set([sign for sign in self.significances if not sign.is_action()])

    def get_components(self):
        components = set()
        for pm in self.images:
            components |= pm.get_signs()
        return components

    def get_own_scripts(self):
        scripts = []
        for pm in self.significances:
            for parent, index in pm.out_links:
                if parent.sign.is_action():
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
