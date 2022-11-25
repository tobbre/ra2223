import math
import inputreader
import lpbp
import lpsd
import utils


def write_iLPsol_of_bitstring(bitstring):
    """
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
    triplet_database = utils.create_triplet_database(num_items=num_items)
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
    triplet_database = utils.create_triplet_database(num_items=num_items)

    lpsd.lp_runner(triplet_database=triplet_database, bitstring=bitstring, sol_name=sol_name)

outputfolder = "out"
filename1 = '%s/20221125-124616_best_species_txt_1.txt' % outputfolder
# filename1 = '%s/best_species_txt_1.txt' % outputfolder
# filename1 = '%s/testitest.txt' % outputfolder
bitstring = inputreader.read_bitstring_from_file(filename=filename1, bitstring_number=0)

write_size_dist_for_bitstring(bitstring=bitstring)

# write_iLPsol_of_bitstring(bitstring)

# print(find_indices_of_1s_in_bitstring(bitstring=bitstring))


