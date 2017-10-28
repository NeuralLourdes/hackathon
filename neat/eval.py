
from __future__ import print_function
import numpy as np
import os
import neat
import random
from functools import partial

import tron
import play_tron
import NN_IO

def run(config_file):
    # Load configuration.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction,
                         neat.DefaultSpeciesSet, neat.DefaultStagnation,
                         config_file)

    # Create the population, which is the top-level object for a NEAT run.
    pop = neat.Population(config)

    # Add a stdout reporter to show progress in the terminal.
    pop.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    pop.add_reporter(stats)
    pop.add_reporter(neat.Checkpointer(5))

    generations = 5

    # SERIAL # 
    #winner = pop.run(play_tron.eval_genomes, generations)

    # PARALLEL # 
    cpu_cores = 1
    winner = pop.run(play_tron.eval_genomes, 1) # first run serial
    
    for n in range(generations):
        goenni = play_tron.genome_parallel(winner)
        pe = neat.ParallelEvaluator(cpu_cores, goenni.eval_fn)
        winner = pop.run(pe.evaluate, 1)


    # Show output of the most fit genome against training data.
    print('\nOutput:')
    winner_net = neat.nn.FeedForwardNetwork.create(winner, config)
    
    play_tron.demo_game(winner_net, winner_net)    
    
    NN_IO.save(winner_net, "beste")

    #p = neat.Checkpointer.restore_checkpoint('neat-checkpoint-4')
    #pop.run(eval_genomes, 10)


if __name__ == '__main__':
    # Determine path to configuration file. This path manipulation is
    # here so that the script will run successfully regardless of the
    # current working directory.
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, 'config-feedforward')
    run(config_path)