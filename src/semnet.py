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

    def copy(self, base, new_base):
        pm, _ = getattr(self.sign, 'add_' + new_base)()
        for event in self.cause:
            pm.cause.append(event.copy(base, new_base))
        for event in self.effect:
            pm.effect.append(event.copy(base, new_base))
        return pm

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
        @return: active PredictionMatrices
        """
        active_pms = []
        if depth > 0:
            for event in itertools.chain(self.cause, self.effect):
                for sign, conn in event.coincidences:
                    if conn > 0:
                        pm = getattr(sign, base + 's')[conn - 1]
                        active_pms.append(pm)
                        if not pm.is_empty():
                            active_pms.extend(pm.spread_down_activity(base, depth - 1))
                    else:
                        pms = getattr(sign, base)
                        active_pms.extend(pms)
                        for pm in pms:
                            active_pms.extend(pm.spread_activity(base, depth - 1))
        return active_pms

    def replace(self, base, old_sign, new_sign):
        for event in itertools.chain(self.cause, self.effect):
            event.replace(base, old_sign, new_sign)


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

    def copy(self, base, new_base):
        e = Event(self.index)
        for sign, conn in self.coincidences:
            pms = getattr(sign, base + 's')
            # TODO: copy through 0 label
            if conn > 0:
                new_pm = pms[conn - 1].copy(base, new_base)
            elif len(pms) == 1:
                new_pm = pms[0].copy(base, new_base)
            else:
                new_pm = None
            _, index = getattr(sign, 'add_' + new_base)(new_pm)
            e.coincidences.add((sign, index))
        return e

    def replace(self, base, old_sign, new_sign):
        pair = None
        for sign, conn in self.coincidences:
            if sign == old_sign:
                pair = (sign, conn)
            else:
                getattr(sign, base + 's')[conn - 1].replace(base, old_sign, new_sign)
        if pair:
            self.coincidences.remove(pair)
            _, new_conn = getattr(new_sign, 'add_' + base)()
            self.coincidences.add((new_sign, new_conn))


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

    def spread_up_activity(self, base, new_base, depth):
        """
        Spread activity up in hierarchy
        @param base: type of semantic net that activity spreads on
        @param new_base: type of semantic net that is used for copying
        @param depth: recursive depth of spreading
        @return: active PredictionMatrices
        """
        active_pms = []
        if depth > 0:
            for pm, indexes in getattr(self, 'out_' + base + 's'):
                if pm.is_causal():
                    active_pms.append(pm.copy(base, new_base))
                else:
                    pms = pm.sign.spread_up_activity(base, new_base, depth - 1)
                    _, index = getattr(self, 'add_' + new_base)()
                    for hpm in pms:
                        hpm.replace(new_base, pm.sign, self)
                        active_pms.append(hpm)
        return active_pms
