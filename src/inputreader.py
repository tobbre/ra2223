
def read_bitstring_from_file(filename, bitstring_number):
    """
    :param filename: filepath of file containing bitstring(s). File may not contain anything else, but immediately start
    with the [ of the first bitstring.
    :param bitstring_number: in case multiple bitstrings are contained in a file, this number is the index of the
    desired bitstring.
    :return:
    """
    with open(filename, 'r') as f:
        data = ''.join(line.rstrip() for line in f)
        data = data.split("]")[bitstring_number]
        data = data.replace("[", "")
        data = data.replace("]", "")
        data = data.replace("\n", "")
        split = data.split(" ")
        bitstring = [int(split[i]) for i in range(len(split))]
    return bitstring


class ParameterTuple():
    def __init__(self, filepath):
        self.num_items = 0
        self.num_generations = 0
        self.learning_rate = 0
        self.num_sessions = 0
        self.learning_percentile = 0
        self.super_percentile = 0
        self.layer1_neurons = 0
        self.layer2_neurons = 0
        self.layer3_neurons = 0
        self.max_allowed_triplets_multiplier = 0
        self.min_allowed_triplets_multiplier = 0

        self.read_parameter_file(filepath=filepath)

    def read_parameter_file(self, filepath):
        with open(filepath, 'r') as fp:
            lines = fp.readlines()
            for i in range(len(lines)):
                if "$" in lines[i]:
                    first_parameter_line = i + 1
                    break
            self.num_items = int(lines[first_parameter_line].split("=")[1].split(";")[0])
            self.num_generations = int(lines[first_parameter_line + 1].split("=")[1].split(";")[0])
            self.learning_rate = lines[first_parameter_line + 2].split("=")[1].split(";")[0]
            self.num_sessions = int(lines[first_parameter_line + 3].split("=")[1].split(";")[0])
            self.learning_percentile = int(lines[first_parameter_line + 4].split("=")[1].split(";")[0])
            self.super_percentile = int(lines[first_parameter_line + 5].split("=")[1].split(";")[0])
            self.layer1_neurons = int(lines[first_parameter_line + 6].split("=")[1].split(";")[0])
            self.layer2_neurons = int(lines[first_parameter_line + 7].split("=")[1].split(";")[0])
            self.layer3_neurons = int(lines[first_parameter_line + 8].split("=")[1].split(";")[0])
            self.max_allowed_triplets_multiplier = float(lines[first_parameter_line + 9].split("=")[1].split(";")[0])
            self.min_allowed_triplets_multiplier = float(lines[first_parameter_line + 10].split("=")[1].split(";")[0])
