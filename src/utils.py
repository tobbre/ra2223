import itertools
import math

def series_to_matrix(series, len_interval):
    matrix = []
    a = len(series) / len_interval
    if a - int(a) != 0:
        raise Exception("The length of the series is not a multiple of the length of each pattern. Something went wrong.")

    for i in range(int(len(series) / len_interval)):
        row_i = []
        for j in range(len_interval):
            row_i.append(series[i * len_interval + j])
        matrix.append(row_i)

    return matrix


def remove_zero_rows(matrix):
    #TODO: Fix this method! It does not do its job. Then write a test about it.
    zero_rows = []
    for i in range(len(matrix)):
        broken = False
        for j in range(len(matrix[i])):
            if matrix[i][j] != 0:
                broken = True
                break
        if broken:
            continue
        zero_rows.append(i)
    for i in zero_rows[::-1]:
        matrix.remove(matrix[i])

    return matrix


def append_complete_patternmatrix_to_txt_file(filepath, pattern_matrix):
    f = open(filepath, "a")
    f.write("\n" * 2)
    f.write("complete pattern_matrix (all allowed patterns, single, double and triplets (bottom of the matrix):\n")
    f.write("Item       ")
    for j in range(len(pattern_matrix[0])):
        f.write("  %s " % j)
    f.write("\n")
    for i in range(len(pattern_matrix)):
        f.write("Pattern %s: " % i)
        for j in range(len(pattern_matrix[i])):
            f.write("  %s " % pattern_matrix[i][j])
        f.write("\n")
    f.close()


def append_used_patterns_to_sol_file(filepath, used_patterns_matrix, used_patterns_indices):
    f = open(filepath, "a")
    f.write("\n" * 2)
    f.write("used patterns (subset of all allowed patterns):\n")
    f.write("Item       ")
    for j in range(len(used_patterns_matrix[0])):
        f.write("  %s " % j)
    f.write("\n")
    for i in range(len(used_patterns_matrix)):
        f.write("Pattern %s: " % used_patterns_indices[i])
        for j in range(len(used_patterns_matrix[i])):
            f.write("  %s " % used_patterns_matrix[i][j])
        f.write("\n")
    f.close()


def create_triplet_database(num_items):
    '''
    Generates all possible triplets using itertools.combinations, and then transforms the resulting triplets of form
    [0, 1, 4] into triplet_bitstrings of form [1, 1, 0, 0, 1].
    :param num_items: number of items to choose from
    :return: An array containing all possible triplet_bitstring arrays based on num_items
    :return: A dictionary: key = (3, 4, 9), value = index of corresponding triplet in triplet_database
    '''
    lis = [i for i in itertools.combinations(range(0, num_items), 3)]   # Note that every element is an array like (3, 4, 9)
    triplet_database = []
    database_index_by_triplet_items = {}
    index = 0
    for triplet in lis:
        triplet_bitstring = []
        position = 0
        for i in range(num_items):
            if position != 3:
                if i != triplet[position]:
                    triplet_bitstring.append(0)
                else:
                    triplet_bitstring.append(1)
                    position += 1
            else:
                triplet_bitstring.append(0)
        triplet_database.append(triplet_bitstring)
        database_index_by_triplet_items[triplet] = index
        index = index + 1


    return triplet_database, database_index_by_triplet_items


def transform_patternbitstring_to_DBbitstring(patternbitstring, triplet_database, database_index_by_triplet_items):
    '''

    :param patternbitstring:
    :param triplet_database: created in utils.create_triplet_database
    :param database_index_by_triplet_items: created in utils.create_triplet_database
    :return:
    '''
    bitstring_as_patterns = series_to_matrix(patternbitstring, int(math.sqrt(len(patternbitstring))))

    # Transforms each n bit pattern of bitstring_as_patterns into "item representation", (3, 4, 9)
    patterns_as_indices = [[i for i in range(len(pattern)) if pattern[i] == 1] for pattern in bitstring_as_patterns]

    # Adds penalty for non-triplets (used for neuralnetwork1.py, if not needed simply ignore the output)
    extra_penalty = 0
    for pattern in patterns_as_indices:
        extra_penalty -= abs(len(pattern) - 3)

    # Replaces bitstring by a database bitstring (i.e. bitstring[i]=1 ==> triplet_database[i] is allowed)
    num_triplets = len(triplet_database)
    bitstring = [0] * num_triplets
    for i in [database_index_by_triplet_items[tuple(pattern)] for pattern in patterns_as_indices if len(pattern) == 3]:
        bitstring[i] = 1

    return bitstring, extra_penalty


def create_implied_bitstring(bitstring, triplet_database, database_index_by_triplet_items):
    '''
    When this method is used, it is assumed that items are ordered ascending by weight, i.e. s1 ≤ s2 ≤ ... ≤ s(num_items).
    This method takes the allowed triplets, and makes sure that all dominated triplets (where 2 items indices are the
    same but one item has a lower index, i.e. the same triplet but one item is swapped for a smaller item) area also allowed.
    :param bitstring:
    :param triplet_database:
    :param database_index_by_triplet_items: python dictionary with key: tuple of items in triplet and value: index of triplet in tripelt_database
    :return: a new_bitstring where all triplets implied by the allowed triplets from bitstring are also allowed
    '''

    def find_1step_dominated_triplets(dominator_index):
        dominator_triplet = triplet_database[dominator_index]  # single triplet, array of length num_items
        dominator_triplet_items = [i for i in range(len(dominator_triplet)) if
                                   dominator_triplet[i] == 1]  # single triplet, array of length 3
        implied_triplets_items = []  # array of triplets, each array of length 3
        for i in range(3):
            a_dominated_item = dominator_triplet_items[i] - 1  # integer
            while a_dominated_item >= 0:
                if (a_dominated_item != dominator_triplet_items[0] and
                        a_dominated_item != dominator_triplet_items[1] and
                        a_dominated_item != dominator_triplet_items[2]):
                    temp_implied_triplet = dominator_triplet_items.copy()  # single triplet, array of length 3
                    temp_implied_triplet[i] = a_dominated_item
                    temp_implied_triplet.sort()
                    implied_triplets_items.append(temp_implied_triplet)
                a_dominated_item = a_dominated_item - 1

        implied_triplets_indices = [database_index_by_triplet_items[tuple(triplet)] for triplet in
                                    implied_triplets_items]  # array of indices, each index corresponds to a triplet in the triplet database

        return implied_triplets_indices
    new_bitstring = bitstring.copy()
    for i in range(len(new_bitstring)-1, -1, -1):
        if new_bitstring[i] == 1:
            implied_triplets_indices = find_1step_dominated_triplets(dominator_index=i)
            for index in implied_triplets_indices:
                new_bitstring[index] = 1
    return new_bitstring


def create_allowed_triplet_matrix(bitstring, triplet_database):
    return [triplet_database[i] for i in range(len(bitstring)) if bitstring[i] == 1]


def create_forbidden_triplet_matrix(bitstring, triplet_database):
    return [triplet_database[i] for i in range(len(bitstring)) if bitstring[i] == 0]


def create_pairs_and_singles_matrix(num_items):
    pns_matrix = []
    for i1 in range(num_items):
        for i2 in range(i1, num_items):
            pattern = []
            for i in range(num_items):
                if i == i1 or i == i2:
                    pattern.append(1)
                else:
                    pattern.append(0)
            pns_matrix.append(pattern)
    return pns_matrix


def clean_sol_file(filepath):
    with open(filepath, 'r+') as fp:
        # read and store all lines into list
        lines = fp.readlines()
        # move file pointer to the beginning of a file
        fp.seek(0)
        # truncate the file
        fp.truncate()

        # start writing lines
        # iterate line and line number
        fp.write(lines[0])
        fp.write(lines[1])
        for line in lines[2:]:
            line = line.replace("\n", "")
            value = abs(float(line.split(" ")[1]))
            if value >= 0.000001:
                fp.write(line + "\n")


def find_used_patterns_indices_from_solfile(filepath):
    used_patterns_indices = []
    with open(filepath, 'r') as fp:
        lines = fp.readlines()
        for line in lines[2:]:
            pattern_index = int(line.split("[")[1].split("]")[0])
            used_patterns_indices.append(pattern_index)
    return used_patterns_indices




