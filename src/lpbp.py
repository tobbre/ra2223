#Linear Programming Solver for the Binpacking problem based on allowed item combinations

from gurobipy import Model, quicksum, GRB, setParam
from math import comb
import utils

setParam('LogToConsole', 0)


def lp_runner_complete(num_items,
                       allowed_triplets=[],
                       pairs_singles_patterns=[],
                       lp_type="LP",
                       sol_name="x"):
    model, pattern_matrix = lp_builder(num_items=num_items,
                                       allowed_triplets=allowed_triplets,
                                       pairs_singles_matrix=pairs_singles_patterns,
                                       lp_type=lp_type)
    model.optimize()
    if sol_name != "x":
        lp_output_sol(model=model,
                      sol_name=sol_name,
                      lp_type=lp_type,
                      pattern_matrix=pattern_matrix)
    return model


def lp_builder(num_items,
               lp_type,
               allowed_triplets=[],
               pairs_singles_matrix=[]):
    p_total_triplets = len(allowed_triplets)
    p_total = p_total_triplets + comb(num_items, 2) + comb(num_items, 1)

    def combine_pattern_matrices():
        """
            :return: A complete pattern matrix containing all usable patterns.
            Note that the indices in the pattern matrix for the triplets do NOT NECESSARILY correspond to the indices
            in of the triplets the bitstring output of the neural network!!!
        """
        pattern_matrix = []
        for i in range(len(pairs_singles_matrix)):
            pattern_matrix.append(pairs_singles_matrix[i])
        for i in range(len(allowed_triplets)):
            pattern_matrix.append(allowed_triplets[i])
        return pattern_matrix

    # Parameters
    pattern_matrix = combine_pattern_matrices()
    m = Model("Naive BinPacking LP")

    # Variables
    pattern_used = {}
    if lp_type == "ILP":
        var_type = GRB.BINARY
    elif lp_type == "LP":
        var_type = GRB.CONTINUOUS

    for p in range(p_total):
        pattern_used[p] = m.addVar(lb=0, ub=1, vtype=var_type, name="pattern_used[%s]" % p)
    m.update()

    # Constraints
    for i in range(num_items):
        m.addConstr(quicksum(pattern_used[p] * pattern_matrix[p][i] for p in range(p_total)) == 1,
                    name="item_coverage_constraint[%s]" % i)
    m.update()

    # Objective
    m.setObjective(quicksum(pattern_used[p] for p in range(p_total)), sense=GRB.MINIMIZE)
    m.update()

    return m, pattern_matrix


def lp_output_sol(model, sol_name, lp_type, pattern_matrix):
    if sol_name != "x":
        filename = "out/%s%s.sol" % (lp_type, sol_name)
        model.write(filename=filename)
        utils.clean_sol_file(filepath=filename)
        used_patterns_indices = utils.find_used_patterns_indices_from_solfile(filepath=filename)
        used_patterns = [pattern_matrix[i] for i in used_patterns_indices]
        utils.append_used_patterns_to_sol_file(filepath=filename,
                                               used_patterns_matrix=used_patterns,
                                               used_patterns_indices=used_patterns_indices)
        utils.append_complete_patternmatrix_to_txt_file(filepath=filename,
                                                        pattern_matrix=pattern_matrix)
