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

    def is_empty(self):
        return len(self.cause) == 0 and len(self.effect) == 0

    def is_causal(self):
        return len(self.effect) > 0

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

    def spread_down_activity(self, base, depth):
        """
        Spread activity down in hierarchy
        @param base: name of semantic net that activity spreads on
        @param depth: recursive depth of spreading
        @return: active chains of PredictionMatrices
        """
        active_chains = []

        def check_pm(pm):
            if not pm.is_empty():
                chains = pm.spread_down_activity(base, depth - 1)
                for chain in chains:
                    active_chains.append([self] + chain)
            else:
                active_chains.append([self, pm])

        if depth > 0:
            for event in itertools.chain(self.cause, self.effect):
                for sign, conn in event.coincidences:
                    if conn > 0:
                        pm = getattr(sign, base + 's')[conn - 1]
                        check_pm(pm)
                    else:
                        pms = getattr(sign, base + 's')
                        for pm in pms:
                            check_pm(pm)
        return active_chains

    def replace(self, base, new_base, old_sign, new_sign):
        pm, idx = getattr(self.sign, 'add_' + new_base)()
        for event in self.cause:
            pm.cause.append(event.replace(base, new_base, old_sign, new_sign))
        for event in self.effect:
            pm.effect.append(event.replace(base, new_base, old_sign, new_sign))
        return pm, idx


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
        for s, _ in self.coincidences:
            if s == sign:
                return True
        return False

    def replace(self, base, new_base, old_sign, new_sign):
        event = Event(self.index)
        for sign, conn in self.coincidences:
            if sign == old_sign:
                event.coincidences.add(getattr(new_sign, 'add_' + new_base))
            else:
                # TODO: spread through 0 conn
                if conn > 0:
                    _, new_conn = getattr(sign, base + 's')[conn - 1].replace(base, new_base, old_sign, new_sign)
                    event.coincidences.add((sign, new_conn))
        return event


class Sign:
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

    def is_abstract(self):
        return len(self.images) == 0

    def add_image(self, pm=None):
        if not pm:
            pm = PredictionMatrix(self, len(self.images) + 1)
        self.images.append(pm)
        return pm, len(self.images)

    def add_significance(self, pm=None):
        if not pm:
            pm = PredictionMatrix(self, len(self.significances) + 1)
        self.significances.append(pm)
        return pm, len(self.significances)

    def add_meaning(self, pm=None):
        if not pm:
            pm = PredictionMatrix(self, len(self.meanings) + 1)
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

    def spread_up_activity_act(self, base, depth):
        """
        Spread activity up in hierarchy
        @param base: type of semantic net that activity spreads on
        @param depth: recursive depth of spreading
        @return: active PredictionMatrices
        """
        active_pms = set()
        if depth > 0:
            for pm, indexes in getattr(self, 'out_' + base + 's'):
                if pm.is_causal():
                    active_pms.add(pm)
                else:
                    pms = pm.sign.spread_up_activity_act(base, depth - 1)
                    active_pms |= pms
        return active_pms

    def spread_up_activity_obj(self, base, depth):
        """
        Spread activity up in hierarchy
        @param base: type of semantic net that activity spreads on
        @param depth: recursive depth of spreading
        @return: active PredictionMatrices
        """
        active_pms = set()
        if depth > 0:
            for pm, indexes in getattr(self, 'out_' + base + 's'):
                if not pm.is_causal():
                    active_pms.add(pm)
                    pms = pm.sign.spread_up_activity_cuas(base, depth - 1)
                    active_pms |= pms
        return active_pms
