
class PRManager(object):
    def __init__(self, pranges):
        self.pranges = pranges

    def calc_prange_probability(self, lst, upper_bound=True, key=None):
        if key is None:
            key = lambda x: x

        total = len(lst)
        if total == 0:
            return 0

        for prange in self.pranges:
            counter = 0
            for item in lst:
                value = key(item)
                if upper_bound and prange.d2 and prange.d2 <= value:
                    continue
                if prange.d1 <= value:
                    counter += 1

            prange.probability = counter / float(total)
        return None

    def index_prange(self, value, upper_bound=True):
        for i, rgroup in enumerate(self.pranges):
            if upper_bound and rgroup.d2 and rgroup.d2 <= value:
                continue
            if rgroup.d1 <= value:
                return i
        return -1


class PRange(object):

    def __init__(self, d1, d2=None, probability=0):
        self.d1 = d1
        self.d2 = d2
        self.probability = probability

    def __str__(self):
        return '{}-{} @ {}'.format(self.d1, self.d2, self.probability)
