# Linear Programming Solver for the Binpacking problem based on allowed item combinations (only maximum triplets as input)


from gurobipy import Model, quicksum, GRB, setParam
from math import comb
import utils
import itertools
import numpy as np

setParam('LogToConsole', 0)


def lp_runner_complete(num_items,
                       maximum_triplets=[],
                       lp_type="LP",
                       sol_name="x"):
    model = lp_builder(num_items=num_items,
                       maximum_triplets=maximum_triplets,
                       lp_type=lp_type)
    model.optimize()
    if sol_name != "x":
        lp_output_sol(model=model,
                      sol_name=sol_name,
                      lp_type=lp_type,
                      maximum_triplets=maximum_triplets)
    return model


def lp_builder(num_items,
               maximum_triplets,
               lp_type):
    # Parameters
    num_maximum_triplets = len(maximum_triplets)
    m = Model("Maximum Pattern BinPacking LP")

    # Variables
    pattern_used = {}

    if lp_type == "ILP":
        var_type = GRB.INTEGER
    elif lp_type == "LP":
        var_type = GRB.CONTINUOUS

    for p in range(num_maximum_triplets):
        pattern_used[p] = m.addVar(lb=0, vtype=var_type, name="pattern_used[%s]" % p)
    m.update()

    # Constraints
    for i in range(num_items-1, -1, -1):
        rhs = num_items - i
        lhs = 0
        for p in range(num_maximum_triplets):
            pattern_intersection_ItemsAfteri = sum(maximum_triplets[p][i:])
            lhs += pattern_used[p] * pattern_intersection_ItemsAfteri
        m.addConstr(lhs >= rhs, name="item_coverage[%s]" % i)

    m.update()

    # Objective
    m.setObjective(quicksum(pattern_used[p] for p in range(num_maximum_triplets)), sense=GRB.MINIMIZE)
    m.update()

    return m


def lp_output_sol(model, sol_name, lp_type, maximum_triplets):
    if sol_name != "x":
        filename = "out/%s%s.sol" % (lp_type, sol_name)
        model.write(filename=filename)
        utils.clean_sol_file(filepath=filename)
        utils.append_maximum_triplets_to_txt_file(filepath=filename, maximum_triplets=maximum_triplets)

