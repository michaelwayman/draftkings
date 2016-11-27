"""
This sub module contains classes to help pick the best lineups.

It contains 2 important classes:

 1. :class:`~basketball.utils.evolution.Evolvable`
 2. :class:`~basketball.utils.evolution.Evolve`

Evolvable in our case, represents a lineup with a cost and expected points.

Evolve is able to generate new lineups (Evolvables) given a pool of players.

"""
import random
from abc import ABCMeta, abstractmethod

from texttable import Texttable
import progressbar


class Evolvable(object):
    """ABC for use with the `Evolve` class.

    :class:`~basketball.utils.evolution.Evolvable` represents an object that has "genes".
    The idea of the Evolvable class is that multiple instances
    can be combined to create new Evolvables.

    After combining Evolvable instances ideally we produce Evolvable
    that are unique from their parents with more desirable genes.
    Not every new combination of Evolvables will be better than their parents,
    but over thousands of generations the new Evolvables should ideally be better.
    """
    __metaclass__ = ABCMeta

    def __init__(self, genes):
        """Subclasses of this ABC should call super on this method

        Args:
            genes: list of the genes that each :class:`~basketball.utils.evolution.Evolvable` must have

        Note:
            please see the code for how to use `_cache` and `cache_properties`
        """
        self._cache = {}
        self.cache_properties = False
        self.genes = {gene: None for gene in genes}

    @abstractmethod
    def can_survive(self):
        """
        Returns:
             A boolean whether or not this :class:`~basketball.utils.evolution.Evolvable`
             can survive in the wild.
             """
        raise NotImplemented

    @abstractmethod
    def fitness_level(self):
        """
        Returns:
            some sort of number that summarizes how desirable this :class:`~basketball.utils.evolution.Evolvable`
            genes are. (The bigger the better)
        """
        raise NotImplemented


class EvolvableLineup(Evolvable):
    """:class:`~basketball.utils.evolution.Evolvable` that is suited for a draftkings basketball lineup."""
    @property
    def expected_points(self):
        """The number of draftking points this lineup is expected to produce"""
        if not self.cache_properties:
            self._cache['expected_points'] = sum(
                [player.expected_points for player in self.genes.values() if player])
        return self._cache['expected_points']

    @property
    def cost(self):
        """How much does this lineup cost in terms of salary"""
        if not self.cache_properties:
            self._cache['cost'] = sum(
                [player.salary for player in self.genes.values() if player])
        return self._cache['cost']

    def can_survive(self):
        """Our lineups cannot survive if they cost more than 50,000"""
        return self.cost <= 50000

    def fitness_level(self):
        """The more draftking points the better the lineup"""
        return self.expected_points


class Evolve(object):
    """Combines :class:`~basketball.utils.evolution.Evolvable`s to create more new and unique Evolvables.

    This class will take a `gene_pool` and will generate random Evolvables from the gene_pool.
    It can then combine those Evolvables to create Evolvables with a new and unique set of genes.
    This process happens iteratively, each time only the best Evolvables are chosen to create new Evolvables from.
    """

    def __init__(self, gene_pool):
        """Initialize the `Evolve` class with a gene pool

        Args:
            gene_pool: A dictionary with "genes" for keys, and a list of "gene_expressions" as the value.

        Note:
            `self.best` an aggregate of the best :class:`~basketball.utils.evolution.Evolvable`s from every generation
            `self.population` represents the current generation and is assigned after every iteration in `run()`
            `self.best` is updated after every iteration in `run()`
        """
        self.gene_pool = gene_pool
        self.population = []
        self.best = []

    def run(self, n=1000, n_best=5, n_children=4):
        """Starts and runs the evolution process.

        1. Create the initial population
        2. Select the 'most fit' from the population and "breed" them, updating the current population
        3. Repeat #2 while keeping track of the "best of all time"

        Args:
            n: the number of generations
            n_children: the number of children each group of parents will produce
            n_print: print the 'best of all time' after every `n_print` generations
        """
        if not self.population:
            self.population = [self.generate_random_parent() for _ in range(n_children)]
            self.set_best()

        bar = progressbar.ProgressBar(min_value=0, max_value=n)

        for i in xrange(n):
            parents = self.best_parents()
            self.population = [self.cross_over(parents) for _ in range(n_children)]
            bar.update(i + 1)

            self.set_best(n_best=n_best)

    def set_best(self, n_best=5):
        """
        Updates the "best of all time" list using the current population.
        """
        self.best = sorted(
            self.best + self.population,
            key=lambda k: k.fitness_level(), reverse=True)[:n_best]

    def best_parents(self, n=2):
        """Select the best n `Evolvable`s from the current population.

        Args:
            n: # of best parents to return

        Returns:
            List of the best `Evolvable`s from the current population.
        """
        return sorted(self.population, key=lambda k: k.fitness_level(), reverse=True)[:n]

    def generate_random_parent(self):
        """Generates a random `Evolvable` using genes from the `gene_pool`.

        Returns:
            Evolvable randomly created from the `gene_pool`
        """
        parent = EvolvableLineup(self.gene_pool.keys())
        while True:
            for gene, expression in self.gene_pool.iteritems():
                while True:
                    random_gene_expression = random.choice(expression)
                    if random_gene_expression not in parent.genes.values():
                        parent.genes[gene] = random_gene_expression
                        break
            if parent.can_survive():
                parent.cache = True
                return parent

    def cross_over(self, parents):
        """Combines 1 or more parents into a single child.

        For each gene in the child this function will choose the expression from a randomly selected parent
        If no such expression is possible then an expression will be selected from the 'gene_pool'

        Args:
            parents (Evolvable): sequence of `Evolvable`s

        Note:
            If no expressions from the `gene_pool` is used then `mutate()` is called on the child.

        Returns:
            Evolvable created by combining the parents and inserting a mutation from the `gene_pool`.
        """
        child = EvolvableLineup(self.gene_pool.keys())

        while True:
            mutated = False

            for gene in self.gene_pool.keys():
                random_parent = random.choice(parents)
                random_gene_expression = random_parent.genes[gene]

                while True:
                    if random_gene_expression not in child.genes.values():
                        child.genes[gene] = random_gene_expression
                        break
                    mutated = True
                    random_gene_expression = random.choice(self.gene_pool[gene])
            if not mutated:
                self.mutate(child)

            if child.can_survive():
                child.cache = True
                return child

    def mutate(self, evolvable, n1=1, n2=2):
        """
        Takes an Evolvable and randomly replaces between n1-n2 of its genes from the gene pool.
        Args:
            evolvable: The Evolvable to mutate
            n1: minimum # of genes to replace
            n2: maximum # of genes to replace

        Returns:
            None
        """
        swap = random.randint(n1, n2)
        for i in range(swap):
            while True:
                random_gene = random.choice(self.gene_pool.keys())
                random_gene_expression = random.choice(self.gene_pool[random_gene])
                if random_gene_expression not in evolvable.genes.values():
                    evolvable.genes[random_gene] = random_gene_expression
                    break

    def __str__(self):
        ret = ''

        for i, lineup in enumerate(self.best):
            ret += 'Lineup {}\n'.format(i + 1)
            ret += '=' * 100 + '\n'

            lineup_actual_score = 0
            lineup_actual_mins = 0
            lineup_avg_mins = 0

            table = Texttable(max_width=130)
            table.set_deco(Texttable.HEADER)
            table.add_row(['Position', 'Name', 'Cost', 'Predicted', 'Actual', 'Mins', 'Avg Mins', 'PPM', 'AVG PPM'])

            for position, player in lineup.genes.items():
                try:
                    game_log = player.gamelog_set.get(game__date=self.date)
                except:
                    game_log = Foo()
                    game_log.draft_king_points = 0
                    game_log.minutes = 0
                    game_log.points_per_min = 0
                game_logs = player.game_logs_last_x_days(90)
                table.add_row([
                    position, player.name, player.salary,
                    player.expected_points, game_log.draft_king_points, game_log.minutes,
                    player.average_minutes(game_logs=game_logs), game_log.points_per_min, player.average_ppm(game_logs=game_logs)
                ])
                lineup_actual_score += game_log.draft_king_points
                lineup_actual_mins += game_log.minutes
                lineup_avg_mins += player.average_minutes()

            lineup.actual = lineup_actual_score
            table.add_row([
                'TOTAL', '', lineup.cost,
                lineup.expected_points, lineup_actual_score, lineup_actual_mins,
                lineup_avg_mins, '', ''
            ])
            ret += table.draw() + '\n'
            ret += '=' * 100 + '\n'
            ret += ', '.join(p.name for p in lineup.genes.values()) + '\n\n\n'
        return ret


class Foo(object):
    pass
