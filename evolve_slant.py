## we are going to attemp to get better at slant boards based
# on GA

from pyevolve import Initializators
from pyevolve import G1DList
from pyevolve import GSimpleGA
from pyevolve import Selectors
from pyevolve import Crossovers
from pyevolve import Mutators

from slants import HeadlessSlantSim, SlantSim
from helpers import get_board_data

import pymunk

from time import time

from guppy import hpy; hp=hpy()

BOARD = 'bigger'
board_data = get_board_data(BOARD)
platform_count = len(board_data.get('platforms'))

#sim_class = SlantSim
sim_class = HeadlessSlantSim

sim = sim_class()

loop_counter = 0
start_time = None

def fitness_test(chromosome):
    global loop_counter
    global start_time
    loop_counter += 1
    # to do the fitness test we are going to need
    # to run a simulation
    sim.reset()
    sim.board_name = BOARD
    sim.populate_from_board()

    for data,angle in zip(sim.platform_data,chromosome):
        print 'angle: %s' % angle
        data['angle'] = angle
    print

    sim.run()
    score = sim.score

    print 'loops/s:',loop_counter/(time()-start_time)

    return score

genome = G1DList.G1DList(platform_count)
genome.setParams(randmin=0,randmax=180)

genome.evaluator.set(fitness_test)

GENERATIONS = 500
POPULATION = 5

ga = GSimpleGA.GSimpleGA(genome)
ga.setGenerations(GENERATIONS)
ga.setPopulationSize(POPULATION)
start_time = time()
ga.evolve(freq_stats=20)

print 'best: %s' % ga.bestIndividual()
