# This file is used to test whether tensorflow works properly in the docker container, without having to run the
# whole neural network. it will import tensorflow, build a small model and create an output file.
import utils
import numpy as np
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import SGD
import time
from math import comb
import inputreader
import math
import lpbp
import lpsd
import sys

'''
Testing Tensorflow 
'''

timestamp = time.strftime("%Y%m%d-%H%M%S")
inputstring = sys.argv[1]
# inputstring = "sampleinputfile.txt"
params = inputreader.ParameterTuple("in/" + inputstring)

num_items = params.num_items
num_decision_vars = comb(num_items, 3)

num_generations = params.num_generations
learning_rate = params.learning_rate
num_sessions = params.num_sessions
learning_percentile = params.learning_percentile
super_percentile = params.super_percentile

layer1_neurons = params.layer1_neurons
layer2_neurons = params.layer2_neurons
layer3_neurons = params.layer3_neurons

num_actions = 2

observation_space = 2 * num_decision_vars
len_game = num_decision_vars
state_dim = (observation_space,)
INF = 1000000

model = Sequential()
model.add(Dense(layer1_neurons, activation="relu"))
model.add(Dense(layer2_neurons, activation="relu"))
model.add(Dense(layer3_neurons, activation="relu"))
model.add(Dense(1, activation="sigmoid"))
model.build((None, observation_space))
model.compile(loss="binary_crossentropy", optimizer=SGD(learning_rate=learning_rate))
# Adam optimizer also works well, with lower learning rate

with open('tttfile.txt', 'w') as f:
    original_stdout = sys.stdout
    sys.stdout = f # Change the standard output to the file we created.
    print(model.summary())
    sys.stdout = original_stdout # Reset the standard output to its original value



'''
Testing Gurobipy
'''
def write_iLPsol_of_bitstring(bitstring):
    """
    This calculates the corresponding ILP and LP solutions of a bitstring and saves them as a <lp_type><sol_name>.sol file.
    :param bitstring:
    :return:
    """

    num_patterns = len(bitstring)
    num_items = 0
    for i in range(num_patterns):
        if math.comb(i, 3) == num_patterns:
            num_items = i
            break
    triplet_database = utils.create_triplet_database(num_items=num_items)[0]
    triplet_matrix = utils.create_allowed_triplet_matrix(bitstring=bitstring, triplet_database=triplet_database)
    pairs_singles_matrix = utils.create_pairs_and_singles_matrix(num_items=num_items)

    lpbp.lp_runner_complete(num_items=num_items,
                                 allowed_triplets=triplet_matrix,
                                 pairs_singles_patterns=pairs_singles_matrix,
                                 lp_type="ILP",
                                 sol_name="testindocker")
    lpbp.lp_runner_complete(num_items=num_items,
                                 allowed_triplets=triplet_matrix,
                                 pairs_singles_patterns=pairs_singles_matrix,
                                 lp_type="LP",
                                 sol_name="testindocker")


outputfolder = "out"
filename1 = '%s/goodrun1_best_species_txt.txt' % outputfolder
# filename1 = '%s/best_species_txt_1.txt' % outputfolder
# filename1 = '%s/testitest.txt' % outputfolder
bitstring = inputreader.read_bitstring_from_file(filename=filename1, bitstring_number=0)
write_iLPsol_of_bitstring(bitstring)

