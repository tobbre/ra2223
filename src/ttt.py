# This file is used to test whether tensorflow works properly in the docker container, without having to run the
# whole neural network. it will import tensorflow, build a small model and create an output file.
import utils
import numpy as np
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import SGD
import time
from math import comb
import lpbp
import lpsd
import inputreader
import sys

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

