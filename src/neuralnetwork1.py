import utils
import numpy as np
import time
from math import comb
import inputreader
import sys
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import SGD
import lpbp


start_time = time.time()
timestamp = time.strftime("%d-%m-%Y_%H:%M")
# f = sys.argv[1]
f = "input_machine1"
params = inputreader.ParameterTuple("in/" + f)
output_folder = "out"
consoleoutput_filepath = ('%s/' % output_folder + timestamp + '_consoleoutput' + '.txt')

num_items = params.num_items
num_decision_vars = comb(num_items, 3)
# The length of the word we are generating.

num_generations = params.num_generations  # 100000 generations should be plenty
learning_rate = params.learning_rate  # Increase this to make convergence faster, decrease if the algorithm gets stuck in local optima too often.
num_sessions = params.num_sessions  # number of new sessions per iteration
learning_percentile = params.learning_percentile  # top 100-X percentile we are learning from
super_percentile = params.super_percentile  # top 100-X percentile that survives to next iteration

layer1_neurons = params.layer1_neurons  # Number of neurons in the hidden layers.
layer2_neurons = params.layer2_neurons
layer3_neurons = params.layer3_neurons

num_actions = 2  # The size of the alphabet. Each decision variables is either 0 or 1.

observation_space = 2 * num_decision_vars  # Leave this at 2*num_decision_vars. The input vector will have size
# 2*num_decision_vars, where the first num_decision_vars letters encode our partial word (with zeros on
# the positions we haven't considered yet), and the next num_decision_vars bits one-hot encode which letter we are
# considering now. So e.g. [0,1,0,0,   0,0,1,0] means we have the partial word 01 and we are considering the third
# letter now.
# Is there a better way to format the input to make it easier for the neural network to understand things?


len_game = num_decision_vars
state_dim = (observation_space,)
INF = 1000000

# Model structure: a sequential network with three hidden layers, sigmoid activation in the output.
# I usually used relu activation in the hidden layers but play around to see what activation function and what
# optimizer works best.
# It is important that the loss is binary cross-entropy if alphabet size is 2.

model = Sequential()
model.add(Dense(layer1_neurons, activation="relu"))
model.add(Dense(layer2_neurons, activation="relu"))
model.add(Dense(layer3_neurons, activation="relu"))
model.add(Dense(1, activation="sigmoid"))
model.build((None, observation_space))
model.compile(loss="binary_crossentropy", optimizer=SGD(learning_rate=learning_rate))
# Adam optimizer also works well, with lower learning rate
# print(model.summary())

triplet_database = utils.create_triplet_database(num_items=num_items)
pairs_singles_matrix = utils.create_pairs_and_singles_matrix(num_items=num_items)


def eval_score(input_bitstring, triplet_database, pairs_singles_matrix):
    """
    Reward function for your problem.
    Input: a 0-1 vector of length num_decision_vars. It represents the graph (or other object) you have created.
    Output: the reward/score for your construction.
    """
    bitstring = [input_bitstring[i] for i in range(int(len(input_bitstring) / 2))]
    num_allowed_triplets = np.sum(bitstring)
    max_allowed_triplets = num_items * params.max_allowed_triplets_multiplier
    min_allowed_triplets = num_items * params.min_allowed_triplets_multiplier
    extra_penalty = 0
    if num_allowed_triplets > max_allowed_triplets:
        extra_penalty += max_allowed_triplets - num_allowed_triplets
    if num_allowed_triplets < min_allowed_triplets:
        extra_penalty += num_allowed_triplets - min_allowed_triplets

    # min_violated_constraints = lpsd.lp_runner(triplet_database=triplet_database, bitstring=bitstring)

    triplet_matrix = utils.create_allowed_triplet_matrix(bitstring=bitstring,
                                                         triplet_database=triplet_database)

    model_ILP = lpbp.lp_runner_complete(num_items=num_items, allowed_triplets=triplet_matrix,
                                        pairs_singles_patterns=pairs_singles_matrix,
                                        lp_type="ILP")
    ilp_value = model_ILP.getObjective().getValue()

    model_LP = lpbp.lp_runner_complete(num_items=num_items, allowed_triplets=triplet_matrix,
                                       pairs_singles_patterns=pairs_singles_matrix,
                                       lp_type="LP")
    lp_value = model_LP.getObjective().getValue()

    return ilp_value - lp_value + extra_penalty # - min_violated_constraints * num_items


################### No need to change anything below here ###################


def generate_session(agent, n_sessions, verbose=1):
    """
    Play n_session games using agent neural network.
    Terminate when games finish

    Code inspired by https://github.com/yandexdataschool/Practical_RL/blob/master/week01_intro/deep_crossentropy_method.ipynb
    """
    states = np.zeros([n_sessions, observation_space, len_game], dtype=int)
    actions = np.zeros([n_sessions, len_game], dtype=int)
    state_next = np.zeros([n_sessions, observation_space], dtype=int)
    prob = np.zeros(n_sessions)
    states[:, num_decision_vars, 0] = 1
    step = 0
    total_score = np.zeros([n_sessions])
    recordsess_time = 0
    play_time = 0
    scorecalc_time = 0
    pred_time = 0
    while (True):
        step += 1
        tic = time.time()
        prob = agent.predict(states[:, :, step - 1], batch_size=n_sessions,
                             verbose=0)  # set verbose=1 to show how long each prediction step takes
        pred_time += time.time() - tic

        for i in range(n_sessions):

            if np.random.rand() < prob[i]:
                action = 1
            else:
                action = 0
            actions[i][step - 1] = action
            tic = time.time()
            state_next[i] = states[i, :, step - 1]
            play_time += time.time() - tic
            if (action > 0):
                state_next[i][step - 1] = action
            state_next[i][num_decision_vars + step - 1] = 0
            if (step < num_decision_vars):
                state_next[i][num_decision_vars + step] = 1
            terminal = step == num_decision_vars
            tic = time.time()
            if terminal:
                total_score[i] = eval_score(state_next[i], triplet_database=triplet_database,
                                            pairs_singles_matrix=pairs_singles_matrix)
            scorecalc_time += time.time() - tic
            tic = time.time()
            if not terminal:
                states[i, :, step] = state_next[i]
            recordsess_time += time.time() - tic

        if terminal:
            break
    # If you want, print out how much time each step has taken. This is useful to find the bottleneck in the program.
    if (verbose):
        print("Predict: " + str(pred_time) + ", play: " + str(play_time) + ", scorecalc: " + str(
            scorecalc_time) + ", recordsess: " + str(recordsess_time))
    return states, actions, total_score


def select_elites(states_batch, actions_batch, rewards_batch, percentile=50):
    """
    Select states and actions from games that have rewards >= percentile
    :param states_batch: list of lists of states, states_batch[session_i][t]
    :param actions_batch: list of lists of actions, actions_batch[session_i][t]
    :param rewards_batch: list of rewards, rewards_batch[session_i]

    :returns: elite_states,elite_actions, both 1D lists of states and respective actions from elite sessions

    This function was mostly taken from https://github.com/yandexdataschool/Practical_RL/blob/master/week01_intro/deep_crossentropy_method.ipynb
    If this function is the bottleneck, it can easily be sped up using numba
    """
    counter = num_sessions * (100.0 - percentile) / 100.0
    reward_threshold = np.percentile(rewards_batch, percentile)

    elite_states = []
    elite_actions = []
    elite_rewards = []
    for i in range(len(states_batch)):
        if rewards_batch[i] >= reward_threshold - 0.0000001:
            if (counter > 0) or (rewards_batch[i] >= reward_threshold + 0.0000001):
                for item in states_batch[i]:
                    elite_states.append(item.tolist())
                for item in actions_batch[i]:
                    elite_actions.append(item)
            counter -= 1
    elite_states = np.array(elite_states, dtype=int)
    elite_actions = np.array(elite_actions, dtype=int)
    return elite_states, elite_actions


def select_super_sessions(states_batch, actions_batch, rewards_batch, percentile=90):
    """
    Select all the sessions that will survive to the next generation
    Similar to select_elites function
    If this function is the bottleneck, it can easily be sped up using numba
    """

    counter = num_sessions * (100.0 - percentile) / 100.0
    reward_threshold = np.percentile(rewards_batch, percentile)

    super_states = []
    super_actions = []
    super_rewards = []
    for i in range(len(states_batch)):
        if rewards_batch[i] >= reward_threshold - 0.0000001:
            if (counter > 0) or (rewards_batch[i] >= reward_threshold + 0.0000001):
                super_states.append(states_batch[i])
                super_actions.append(actions_batch[i])
                super_rewards.append(rewards_batch[i])
                counter -= 1
    super_states = np.array(super_states, dtype=int)
    super_actions = np.array(super_actions, dtype=int)
    super_rewards = np.array(super_rewards)
    return super_states, super_actions, super_rewards


super_states = np.empty((0, len_game, observation_space), dtype=int)
super_actions = np.array([], dtype=int)
super_rewards = np.array([])
sessgen_time = 0
fit_time = 0
score_time = 0


for i in range(num_generations):
    # generate new sessions
    # performance can be improved with joblib
    tic = time.time()
    sessions = generate_session(model, num_sessions,
                                0)  # change 0 to 1 to print out how much time each step in generate_session takes
    sessgen_time = time.time() - tic
    tic = time.time()

    states_batch = np.array(sessions[0], dtype=int)
    actions_batch = np.array(sessions[1], dtype=int)
    rewards_batch = np.array(sessions[2])
    states_batch = np.transpose(states_batch, axes=[0, 2, 1])

    states_batch = np.append(states_batch, super_states, axis=0)

    if i > 0:
        actions_batch = np.append(actions_batch, np.array(super_actions), axis=0)
    rewards_batch = np.append(rewards_batch, super_rewards)

    randomcomp_time = time.time() - tic
    tic = time.time()

    elite_states, elite_actions = select_elites(states_batch, actions_batch, rewards_batch,
                                                percentile=learning_percentile)  # pick the sessions to learn from
    select1_time = time.time() - tic

    tic = time.time()
    super_sessions = select_super_sessions(states_batch, actions_batch, rewards_batch,
                                           percentile=super_percentile)  # pick the sessions to survive
    select2_time = time.time() - tic

    tic = time.time()
    super_sessions = [(super_sessions[0][i], super_sessions[1][i], super_sessions[2][i]) for i in
                      range(len(super_sessions[2]))]
    super_sessions.sort(key=lambda super_sessions: super_sessions[2], reverse=True)
    select3_time = time.time() - tic

    tic = time.time()
    model.fit(elite_states, elite_actions, verbose=0)  # learn from the elite sessions
    fit_time = time.time() - tic

    tic = time.time()

    super_states = [super_sessions[i][0] for i in range(len(super_sessions))]
    super_actions = [super_sessions[i][1] for i in range(len(super_sessions))]
    super_rewards = [super_sessions[i][2] for i in range(len(super_sessions))]

    rewards_batch.sort()
    mean_all_reward = np.mean(rewards_batch[-100:])
    mean_best_reward = np.mean(super_rewards)

    score_time = time.time() - tic


    # print("\n" + str(i) + ". Best individuals: " + str(np.flip(np.sort(super_rewards))))

    # uncomment below line to print out how much time each step in this loop takes.
    # print("Mean reward: " + str(mean_all_reward) + "\nSessgen: " + str(sessgen_time) + ", other: " + str(
    #     randomcomp_time) + ", select1: " + str(select1_time) + ", select2: " + str(select2_time) + ", select3: " + str(
    #     select3_time) + ", fit: " + str(fit_time) + ", score: " + str(score_time))

    def append_params_to_file(f, params):
        f.write(str(params.num_items) + "\n" +
                str(params.num_generations) + "(Generations finished so far: " + str(i) + ")" + "\n" +
                str(params.learning_rate) + "\n" +
                str(params.num_sessions) + "\n" +
                str(params.learning_percentile) + "\n" +
                str(params.super_percentile) + "\n" +
                str(params.layer1_neurons) + "\n" +
                str(params.layer2_neurons) + "\n" +
                str(params.layer3_neurons) + "\n" +
                str(params.max_allowed_triplets_multiplier) + "\n" +
                str(params.min_allowed_triplets_multiplier) + "\n$\n"
                )

    with open(consoleoutput_filepath, 'a') as c:
        sys.stdout = c  # Change the standard output to the file we created.
        sys.stderr = c
        end_time = time.time()
        print("Generation %s. %s\n" % (i, end_time - start_time))
        start_time = end_time
        time.sleep(10)
        if i % 20 == 1:  # Write all important info to files every 20 iterations
            # with open('%s/best_species_pickle_' % output_folder + '.txt', 'wb') as fp:
            #     pickle.dump(super_actions, fp)
            print("----Generation %s----" % i)
            print("\n" + str(i) + ". Best individuals: " + str(np.flip(np.sort(super_rewards))))
            print("Mean reward: " + str(mean_all_reward) + "\nSessgen: " + str(sessgen_time) + ", other: " + str(
                randomcomp_time) + ", select1: " + str(select1_time) + ", select2: " + str(
                select2_time) + ", select3: " + str(
                select3_time) + ", fit: " + str(fit_time) + ", score: " + str(score_time))
            with open('%s/' % output_folder + timestamp + '_best_species.txt', 'w') as f:
                append_params_to_file(f, params)
                for item in super_actions:
                    f.write(str(item))
                    f.write("\n")
            with open('%s/' % output_folder + timestamp + '_best_species_rewards.txt', 'w') as f:
                append_params_to_file(f, params)
                for item in super_rewards:
                    f.write(str(item))
                    f.write("\n")
        if i % 200 == 2:  # To create a timeline, like in Figure 3
            with open('%s/' % output_folder + timestamp + '_best_species_timeline.txt', 'a') as f:
                append_params_to_file(f, params)
                f.write(str(super_rewards[0]))
                f.write(str(super_actions[0]))
                f.write("\n")

        sys.stdout = sys.__stdout__ # Reset the standard output to its original value
        sys.stderr = sys.__stderr__