import itertools, logging


class CausalMatrix:
    """
    Causal matrix - main structure in causal network defining causal and hierarchical relations
    cause - is the list of causal events at each moment
    effect - is the list of effect events at each moment (can be empty)
    """

    def __init__(self, sign=None, uid=None, cause=None, effect=None):
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
        return '{0}:{1}'.format(str(self.sign), str(self.uid))

    def __repr__(self):
        return '<CausalMatrix {0}:{1} [{2}]->[{3}]>'.format(self.sign.name, self.uid,
                                                            ','.join(map(repr, self.cause)),
                                                            ','.join(map(repr, self.effect)))

    def __eq__(self, other):
        return self.sign == other.sign and self.uid == other.uid

    def __hash__(self):
        if self.sign:
            return 3 * hash(self.uid) + 5 * hash(self.sign)
        else:
            return hash(self.uid)

    def __contains__(self, sign):
        for event in itertools.chain(self.cause, self.effect):
            if sign in event:
                return True

        return False

    def add_event(self, event, effect=False):
        mult, part = (-1, self.effect) if effect else (1, self.cause)

        index = (len(part) + 1) * mult
        part.append(event)

        return index

    def get_event(self, link):
        d, part = (link - 1, self.cause) if link > 0 else (-1 * link - 1, self.effect)
        return part[d]

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

    def is_causal(self):
        return len(self.effect) > 0

    def includes(self, base, smaller):
        for event in smaller.cause:
            for se in self.cause:
                if event.resonate(base, se):
                    break
            else:
                return False

        for event in smaller.effect:
            for se in self.effect:
                if event.resonate(base, se):
                    break
            else:
                return False

        return True

    def copy_replace(self, base, new_base, old_sign=None, new_sign=None):
        pm, idx = getattr(self.sign, 'add_' + new_base)()
        for event in self.cause:
            pm.cause.append(event.copy_replace(pm, base, new_base, old_sign, new_sign))
        for event in self.effect:
            pm.effect.append(event.copy_replace(pm, base, new_base, old_sign, new_sign))
        return pm, idx

    def resonate(self, base, pm, check_sign=True, check_order=True):
        if check_sign and not self.sign == pm.sign:
            return False
        if not len(self.cause) == len(pm.cause) or not len(self.effect) == len(pm.effect):
            return False
        if check_order:
            for e1, e2 in zip(itertools.chain(self.cause, self.effect), itertools.chain(pm.cause, pm.effect)):
                if not e1.resonate(base, e2):
                    return False
        else:
            for e1 in self.cause:
                for e2 in pm.cause:
                    if e1.resonate(base, e2, check_order):
                        break
                else:
                    return False
            for e1 in self.effect:
                for e2 in pm.effect:
                    if e1.resonate(base, e2, check_order):
                        break
                else:
                    return False
        return True

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

    def resonate(self, base, event, check_order=True):
        if not len(self.coincidences) == len(event.coincidences):
            return False
        signs = {s: c for s, c in event.coincidences}
        for sign, conn in self.coincidences:
            if sign not in signs:
                return False
            else:
                pm1 = getattr(sign, base + 's')[conn - 1]
                pm2 = getattr(sign, base + 's')[signs[sign] - 1]
                if not pm1.resonate(base, pm2, True, check_order):
                    return False
        return True

    def copy_replace(self, parent, base, new_base, old_sign=None, new_sign=None):
        event = Event(self.index)
        for sign, conn in self.coincidences:
            if old_sign and sign == old_sign:
                # TODO: if new component is composite?
                _, new_conn = getattr(new_sign, 'add_' + new_base)()
                event.coincidences.add((new_sign, new_conn))
                getattr(new_sign, 'add_out_'+new_base)(parent, self.index)
            else:
                # TODO: spread through 0 conn
                if conn > 0:
                    _, new_conn = getattr(sign, base + 's')[conn - 1].copy_replace(base, new_base, old_sign, new_sign)
                    event.coincidences.add((sign, new_conn))
                    getattr(sign, 'add_out_' + new_base)(parent, self.index)
                elif len(getattr(sign, base + 's')) == 1:
                    _, new_conn = getattr(sign, base + 's')[0].copy_replace(base, new_base, old_sign, new_sign)
                    event.coincidences.add((sign, new_conn))
                    getattr(sign, 'add_out_' + new_base)(parent, self.index)
                else:
                    _, new_conn = getattr(sign, 'add_' + new_base)()
                    event.coincidences.add((sign, new_conn))
                    getattr(sign, 'add_out_' + new_base)(parent, self.index)
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
        if hasattr(self, 'name'):  # pickle call hash during loading before instantiating
            return hash(self.name)
        else:
            return object.__hash__(self)

    def is_abstract(self):
        return len(self.images) == 0

    def add_image(self, pm=None):
        if not pm:
            pm = CausalMatrix(self, len(self.images) + 1)
        else:
            pm.uid = len(self.images) + 1
        self.images.append(pm)
        return pm, len(self.images)

    def add_significance(self, pm=None):
        if not pm:
            pm = CausalMatrix(self, len(self.significances) + 1)
        else:
            pm.uid = len(self.significances) + 1
        self.significances.append(pm)
        return pm, len(self.significances)

    def add_meaning(self, pm=None):
        if not pm:
            pm = CausalMatrix(self, len(self.meanings) + 1)
        else:
            pm.uid = len(self.meanings) + 1
        self.meanings.append(pm)
        return pm, len(self.meanings)

    def remove_meaning(self, pm):
        for cm in self.meanings:
            if cm.uid > pm.uid:
                cm.uid -= 1
        for fpm, indexes in self.out_meanings:
            for d in indexes:
                event = fpm.get_event(d)
                for s, i in event.coincidences.copy():
                    if s == self and i > pm.uid:
                        event.coincidences.remove((s, i))
                        event.coincidences.add((s, i - 1))
                        break

        self.meanings.remove(pm)
        for event in itertools.chain(pm.cause, pm.effect):
            for s, conn in event.coincidences:
                s.remove_meaning(s.meanings[conn - 1])

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
