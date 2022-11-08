import itertools

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
    # TODO: Fix this method! It does not do its job. Then write a test about it.
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
    f.write("complete pattern_matrix:\n")
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
    f.write("used patterns:\n")
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
    lis = [i for i in itertools.combinations(range(0, num_items), 3)]
    triplet_database = []
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

    return triplet_database


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
