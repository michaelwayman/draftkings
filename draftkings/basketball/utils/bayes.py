
class PManager(object):
    def __init__(self, rgroups):
        self.rgroups = rgroups

    def calc_rgroup_probability(self, lst, upper_bound=True, key=None):
        if key is None:
            key = lambda x: x

        total = len(lst)
        if total == 0:
            return 0

        for rgroup in self.rgroups:
            counter = 0
            for item in lst:
                value = key(item)
                if upper_bound and rgroup.d2 and rgroup.d2 <= value:
                    continue
                if rgroup.d1 <= value:
                    counter += 1

            rgroup.probability = counter / float(total)

    def rgroup(self, value, upper_bound=True):
        for i, rgroup in enumerate(self.rgroups):
            if upper_bound and rgroup.d2 and rgroup.d2 <= value:
                continue
            if rgroup.d1 <= value:
                return i
        return -1


class RGroup(object):

    def __init__(self, d1, d2=None, probability=0.00001):
        self.d1 = d1
        self.d2 = d2
        self.probability = probability

    def __str__(self):
        return '{}-{} @ {}'.format(self.d1, self.d2, self.probability)
