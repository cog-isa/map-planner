import itertools


class CausalMatrix:
    """
    Causal matrix - main structure in causal network defining causal and hierarchical relations
    cause - is the list of causal events at each moment
    effect - is the list of effect events at each moment (can be empty)
    """

    def __init__(self, sign=None, index=None, cause=None, effect=None):
        self.sign = sign
        self.index = index
        if not cause:
            self.cause = []
        else:
            self.cause = cause
        if not effect:
            self.effect = []
        else:
            self.effect = effect

    def __str__(self):
        return '{0}:{1}'.format(str(self.sign), str(self.index))

    def __repr__(self):
        return '{0}:{1}'.format(str(self.sign), str(self.index))

    def __eq__(self, other):
        return self.sign == other.sign and self.index == other.index

    def __hash__(self):
        if self.sign:
            return 3 * hash(self.index) + 5 * hash(self.sign)
        else:
            return hash(self.index)

    def __contains__(self, sign):
        for event in itertools.chain(self.cause, self.effect):
            if sign in event:
                return True

        return False

    def longstr(self):
        return '{0}:{1}->{2}'.format(str(self.sign), '|'.join([str(e) for e in self.cause]),
                                     '|'.join([str(e) for e in self.effect]))

    def add_event(self, event, effect=False):
        mult, part = (-1, self.effect) if effect else (1, self.cause)

        order = (len(part) + 1) * mult
        part.append(event)

        return order

    def get_event(self, order):
        d, part = (order - 1, self.cause) if order > 0 else (-1 * order - 1, self.effect)
        return part[d]

    def add_feature(self, cm, order=None, effect=False, zero_out=False):
        """
        Add causal matrix cm in the new or existed in order event
        @param zero_out: special case of undefined out
        @param cm: causal matrix to add
        @param order: order of existed event
        @param effect: if to add as effect
        @return:
        """
        connector = Connector(self.sign, cm.sign, self.index, cm.index, order)
        mult, part = (-1, self.effect) if effect else (1, self.cause)

        if order is None:
            connector.in_order = (len(part) + 1) * mult # a4:1 -> 1
            part.append(Event(connector.in_order, {connector}))
        else:
            part[abs(order) - 1].coincidences.add(connector)
        if zero_out:
            connector.out_index = 0
        return connector

    def add_execution(self, motor, order=None):
        """
        Add motor function to existed in order
        @param motor: shortcode of handler function to some physic enviroment
        @param order: order of motor function
        @return:
        """
        actions = self.cause
        actuator = Actuator(self.sign, motor, order)
        if order is None:
            actuator.in_order = len(actions) + 1
            actions.append(Event(actuator.in_order, {actuator}))
        else:
            actions[order-1].coincidences.add(actuator)
        return actuator


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

    def copy(self, base, new_base, copied=None):
        if copied is None:
            copied = {}
        pm = getattr(self.sign, 'add_' + new_base)()
        for event in self.cause:
            pm.cause.append(event.copy(pm, base, new_base, copied))
        for event in self.effect:
            pm.effect.append(event.copy(pm, base, new_base, copied))
        return pm

    def expand(self, base, copied=None):
        if copied is None:
            copied = {}
        cm = getattr(self.sign, 'add_' + base)()
        for event in self.cause:
            cm.cause.extend(event.expand(cm, base, copied))
        for event in self.effect:
            cm.effect.extend(event.expand(cm, base, copied))
        return cm

    def replace(self, base, old_sign, new_cm, deleted=None):
        if deleted is None:
            deleted = []
        for event in self.cause:
            event.replace(base, old_sign, new_cm, deleted)
        for event in self.effect:
            event.replace(base, old_sign, new_cm, deleted)

    def resonate(self, base, pm, check_order=True, check_sign=True):
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

    # def check_applicable_by_agent(self, pm, agents):
    #     result = False
    #     for event in self.cause:
    #         for connector in event.coincidences:
    #             if connector.out_sign.name == "holding":
    #                 scm = self.get_ev_signs(event)
    #                 for event_pm in pm.cause:
    #                     for connector in event_pm.coincidences:
    #                         if connector.out_sign.name == "holding":
    #                             pcm = self.get_ev_signs(event_pm)
    #                             raz = list(scm - pcm)
    #                             if len(raz) == 1 and raz[0] in agents or not len(raz):
    #                                 result = True
    #                                 break
    #                     if result:
    #                         break
    #             if result:
    #                 break
    #
    #     return result
    #


    def get_signs(self):
        signs = set()
        for event in itertools.chain(self.cause, self.effect):
            for connector in event.coincidences:
                signs.add(connector.out_sign)
        return signs

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
                for connector in event.coincidences:
                    if connector.out_index > 0:
                        # connector.out_sign with index
                        pm = connector.get_out_cm(base)
                        check_pm(pm)
                    else:
                        pms = getattr(connector.out_sign, base + 's')
                        for index, pm in pms.items():
                            check_pm(pm)
        return active_chains


class Event:
    """
    Event - the set of coincident connectors
    """

    def __init__(self, order, coincidences=None):
        self.order = order
        if not coincidences:
            self.coincidences = set()
        else:
            self.coincidences = coincidences

    def __str__(self):
        return '{{{0}}}'.format(','.join(str(x) for x in self.coincidences))

    def __repr__(self):
        return '{{{0}}}'.format(','.join(str(x) for x in self.coincidences))

    def __eq__(self, other):
        return self.coincidences == other.coincidences

    def __contains__(self, sign):
        for connector in self.coincidences:
            if connector.out_sign == sign:
                return True
        return False

    def add_coincident(self, base, connector):
        self.coincidences.add(connector)
        getattr(connector.out_sign, 'add_out_' + base)(connector)

    def resonate(self, base, event, check_order=True):
        if not len(self.coincidences) == len(event.coincidences):
            return False
        for connector in self.coincidences:
            for conn in event.coincidences:
                if connector.out_sign == conn.out_sign:
                    break
            else:
                return False
            pm1 = connector.get_out_cm(base)
            pm2 = conn.get_out_cm(base)
            if not pm1.resonate(base, pm2, check_order):
                return False
        return True

    def copy(self, new_parent, base, new_base, copied):
        if copied is None:
            copied = {}
        event = Event(self.order)
        for connector in self.coincidences:
            if connector.out_index == 0:
                cm = getattr(connector.out_sign, 'add_' + new_base)()
            else:
                pm = connector.get_out_cm(base)
                if pm not in copied:
                    cm = pm.copy(base, new_base, copied)
                    copied[pm] = cm
                else:
                    cm = copied[pm]
            conn = Connector(new_parent.sign, connector.out_sign, new_parent.index, cm.index, event.order)
            event.add_coincident(new_base, conn)
        return event

    def expand(self, new_parent, base, copied, effect=False):
        events = []
        for conn in self.coincidences:
            if conn.out_index == 0:
                raise Exception('Cannot expand throw zero connection')
            else:
                cm = conn.get_out_cm(base)
                part = cm.effect if effect else cm.cause
                for event in part:
                    events.append(event.copy(new_parent, base, base, copied))
        return events

    def replace(self, base, old_sign, new_cm, deleted):
        for connector in self.coincidences:
            if connector.out_sign == old_sign:
                if connector.out_index not in deleted:
                    getattr(old_sign, 'remove_' + base)(connector.get_out_cm(base))
                    deleted.append(connector.out_index)
                connector.out_sign = new_cm.sign
                connector.out_index = new_cm.index
            else:
                connector.get_out_cm(base).replace(base, old_sign, new_cm, deleted)
    def get_signs(self):
        scm = set()
        for connector in self.coincidences:
            scm.add(connector.out_sign)
        return scm

class Connector:
    """
    Connector - link between to sign components with marker (in_index, in_order, out_index)
    """

    def __init__(self, in_sign, out_sign, in_index, out_index=None, in_order=None):
        self.in_sign = in_sign
        self.out_sign = out_sign

        self.in_index = in_index
        self.in_order = in_order

        self.out_index = out_index

    def __str__(self):
        return '{0}:{1}->{2}'.format(self.out_sign, self.out_index, self.in_order)

    def __repr__(self):
        return '{0}:{1}-{2}->{3}:{4}'.format(self.out_sign, self.out_index, self.in_order, self.in_sign, self.in_index)

    def out_eq(self, other):
        return self.out_sign == other.out_sign and self.out_index == other.out_index

    def in_eq(self, other):
        return self.in_sign == other.in_sign and self.in_index == other.in_index and self.in_order == other.in_order

    def get_out_cm(self, base):
        if self.out_index > 0:
            return getattr(self.out_sign, base + 's')[self.out_index]
        else:
            raise Exception('In connector {0} you cannot get out causal matrix'.format(self))

    def get_in_cm(self, base):
        return getattr(self.in_sign, base + 's')[self.in_index]

class Actuator:
    """
    Actuator - link between sign and motor function with order marker
    """

    def __init__(self, in_sign, motor, in_order=None):
        self.in_sign = in_sign
        self.motor = motor
        self.in_order = in_order

    def __str__(self):
        return '{0}:{1}->{2}'.format(self.in_sign, self.motor, self.in_order)
    def __repr__(self):
        return '{0}->{1}:{2}'.format(self.in_sign, self.motor, self.in_order)

class Sign:
    def __init__(self, name):
        self.name = name
        self.images = {}
        self.significances = {}
        self.meanings = {}
        self.out_significances = []
        self.out_images = []
        self.out_meanings = []

        self._next_image = 1
        self._next_significance = 1
        self._next_meaning = 1

    def __str__(self):
        return '"{0}"'.format(self.name)

    def __repr__(self):
        return '"{0}"'.format(self.name)

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
            pm = CausalMatrix(self, self._next_image)
        else:
            pm.index = self._next_image
        self.images[pm.index] = pm
        self._next_image += 1
        return pm

    def add_significance(self, pm=None):
        if not pm:
            pm = CausalMatrix(self, self._next_significance)
        else:
            pm.index = self._next_significance
        self.significances[pm.index] = pm
        self._next_significance += 1
        return pm

    def add_meaning(self, pm=None):
        if not pm:
            # создается каузальная матрица личностных смыслов
            pm = CausalMatrix(self, self._next_meaning)
        else:
            pm.index = self._next_meaning
        self.meanings[pm.index] = pm
        self._next_meaning += 1
        return pm


    def add_out_significance(self, connector):
        self.out_significances.append(connector)

    def add_out_image(self, connector):
        self.out_images.append(connector)

    def add_out_meaning(self, connector):
        self.out_meanings.append(connector)

    def remove_meaning(self, cm, deleted=None):
        if deleted is None:
            deleted = []
        for event in cm.cause:
            for connector in event.coincidences:
                if (connector.out_sign, connector.out_index) not in deleted:
                    connector.out_sign.remove_meaning(connector.get_out_cm('meaning'), deleted)
                    deleted.append((connector.out_sign, connector.out_index))
        for event in cm.effect:
            for connector in event.coincidences:
                if (connector.out_sign, connector.out_index) not in deleted:
                    connector.out_sign.remove_meaning(connector.get_out_cm('meaning'), deleted)
                    deleted.append((connector.out_sign, connector.out_index))

        for connector in self.out_meanings.copy():
            if connector.out_index == cm.index:
                self.out_meanings.remove(connector)

        del self.meanings[cm.index]

    def spread_up_activity_act(self, base, depth):
        """
        Spread activity up in hierarchy
        @param base: type of semantic net that activity spreads on
        @param depth: recursive depth of spreading
        @return: active PredictionMatrices
        """
        active_pms = set()
        if depth > 0:
            for connector in getattr(self, 'out_' + base + 's'):
                if connector.get_in_cm(base).is_causal():
                    active_pms.add(connector.get_in_cm(base))
                else:
                    pms = connector.in_sign.spread_up_activity_act(base, depth - 1)
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
            for connector in getattr(self, 'out_' + base + 's'):
                if not connector.get_in_cm(base).is_causal():
                    active_pms.add(connector.get_in_cm(base))
                    pms = connector.in_sign.spread_up_activity_obj(base, depth - 1)
                    active_pms |= pms
        return active_pms

    def spread_up_activity_motor(self, base, depth):
        """
        @param base: type a variations of function realization threw semantic net
        @param depth: recursive depth of spreading
        @return: dict of PM and functions that they are implemented in
        """
        actions = set()
        if depth > 0:
            for actuator in getattr(self, 'out_' + base + 's'):
                if hasattr(actuator, 'motor'):
                    actions.add((actuator.in_sign, actuator.motor))
                else:
                    pms = actuator.in_sign.spread_up_activity_motor(base, depth-1)
                    actions |= pms
        return actions

    def find_attribute(self):
        attribute = []
        for connector in self.out_significances:
            if not connector.in_sign.name == "object":
                attribute.append(connector.in_sign)
        return attribute[0]

    def get_role(self):
        sub_role = set()
        for con in self.out_significances:
            sub_role.add(con.in_sign)
        return sub_role