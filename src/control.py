import itertools
import math
import random
import time
import inputreader
import lpbp
import lpsd
import utils


def write_iLPsol_of_bitstring1(bitstring):
    """
    BITSTRING MUST BE IN DATABASE BITSTRING FORMAT
    This calculates the corresponding ILP and LP solutions of a bitstring and saves them as .sol files.
    :param bitstring:
    :return:
    """

    num_patterns = len(bitstring)
    num_items = 0
    for i in range(num_patterns):
        if math.comb(i, 3) == num_patterns:
            num_items = i
            break
    triplet_database, database_index_by_triplet_items = utils.create_triplet_database(num_items=num_items)
    bitstring = utils.create_implied_bitstring(bitstring=bitstring,
                                               triplet_database=triplet_database,
                                               database_index_by_triplet_items=database_index_by_triplet_items)
    triplet_matrix = utils.create_allowed_triplet_matrix(bitstring=bitstring, triplet_database=triplet_database)
    pairs_singles_matrix = utils.create_pairs_and_singles_matrix(num_items=num_items)

    lpbp.lp_runner_complete(num_items=num_items,
                            allowed_triplets=triplet_matrix,
                            pairs_singles_patterns=pairs_singles_matrix,
                            lp_type="ILP",
                            sol_name="test")
    lpbp.lp_runner_complete(num_items=num_items,
                            allowed_triplets=triplet_matrix,
                            pairs_singles_patterns=pairs_singles_matrix,
                            lp_type="LP",
                            sol_name="test")


def write_iLPsol_of_bitstring2(bitstring):
    """
    BITSTRING MUST BE IN PATTERN BITSTRING FORMAT (with num_items^2 bits)
    This calculates the corresponding ILP and LP solutions of a bitstring and saves them as .sol files.
    :param bitstring:
    :return:
    """

    num_items = int(math.sqrt(len(bitstring)))
    triplet_database, database_index_by_triplet_items = utils.create_triplet_database(num_items=num_items)
    bitstring = utils.transform_patternbitstring_to_DBbitstring(patternbitstring=bitstring,
                                                                triplet_database=triplet_database, \
                                                                database_index_by_triplet_items=database_index_by_triplet_items)[0]
    bitstring = utils.create_implied_bitstring(bitstring=bitstring,
                                               triplet_database=triplet_database,
                                               database_index_by_triplet_items=database_index_by_triplet_items)
    triplet_matrix = utils.create_allowed_triplet_matrix(bitstring=bitstring, triplet_database=triplet_database)
    pairs_singles_matrix = utils.create_pairs_and_singles_matrix(num_items=num_items)

    lpbp.lp_runner_complete(num_items=num_items,
                            allowed_triplets=triplet_matrix,
                            pairs_singles_patterns=pairs_singles_matrix,
                            lp_type="ILP",
                            sol_name="test")
    lpbp.lp_runner_complete(num_items=num_items,
                            allowed_triplets=triplet_matrix,
                            pairs_singles_patterns=pairs_singles_matrix,
                            lp_type="LP",
                            sol_name="test")


def find_indices_of_1s_in_bitstring(bitstring):
    """
    :param bitstring:
    :return: Indices of 1s in the bitstring starting with index 0.
    """
    indices = []
    for i in range(len(bitstring)):
        if bitstring[i] == 1:
            indices.append(i)

    return indices


def write_size_dist_for_bitstring(bitstring, sol_name="test"):
    num_patterns = len(bitstring)
    num_items = 0
    for i in range(num_patterns):
        if math.comb(i, 3) == num_patterns:
            num_items = i
            break
    triplet_database = utils.create_triplet_database(num_items=num_items)[0]

    lpsd.lp_runner(triplet_database=triplet_database, bitstring=bitstring, sol_name=sol_name)


def write_triplet_database(num_items):
    triplet_database = utils.create_triplet_database(num_items=num_items)[0]
    print("          ", end='')
    for j in range(len(triplet_database[0])):
        print("  %s " % j, end='')
    print()
    for i in range(len(triplet_database)):
        print("Pattern %s:" % i, end='')
        for j in range(len(triplet_database[i])):
            print("  %s " % triplet_database[i][j], end='')
        print()


outputfolder = "out"
# filename1 = '%s/28-11-2022_00:37_best_species_txt_1.txt' % outputfolder
# filename1 = '%s/best_species_txt_1.txt' % outputfolder
filename1 = '%s/20-12-2022_14:46_best_species.txt' % outputfolder
bitstring = inputreader.read_bitstring_from_file(filename=filename1, bitstring_number=0)

# write_iLPsol_of_bitstring2(bitstring)



#----- The following is to test whether there are instances of implied bitstrings that produce infeasible instances regarding weight distributions
num_items = 15
triplet_database, database_index_by_triplet_items = utils.create_triplet_database(num_items=num_items)
for i in range (100000):
    max_num_ones = random.randint(1, 5)
    bitstring = [0] * 455
    for j in range(max_num_ones):
        bitstring[random.randint(1, math.comb(15, 3)) - 1] = 1

    bitstring = utils.create_implied_bitstring(bitstring=bitstring,
                                       triplet_database=triplet_database,
                                       database_index_by_triplet_items=database_index_by_triplet_items)

    lpsd.lp_runner(triplet_database=triplet_database, bitstring=bitstring)
    if i%100==0:
        print(i)
