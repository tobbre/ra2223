#Linear Programming Solver for finding valid size distributions for a collection of allowed triplets

from gurobipy import Model, quicksum, GRB, setParam
import utils
import numpy as np

def lp_runner(triplet_database=[],
              bitstring=[],
              sol_name="x"):
    model = lp_builder(triplet_database=triplet_database,
                       bitstring=bitstring)
    model.optimize()

    if model.getAttr("Status") == 2:
        if sol_name != "x":
            model.write(filename="out/sizedist%s.sol" % sol_name)
    else:
        print("---!!!Infeasible Instance!!!---")
        return len(bitstring)


    return model.getAttr("ObjVal")

def lp_builder(triplet_database,
               bitstring):

    # Parameters
    allowed_triplets = utils.create_allowed_triplet_matrix(bitstring=bitstring,
                                                           triplet_database=triplet_database)
    forbidden_triplets = utils.create_forbidden_triplet_matrix(bitstring=bitstring,
                                                               triplet_database=triplet_database)

    m = Model("Size Distribution Finder")

    # Variables
    item_size = {}
    for i in range(len(triplet_database[0])):
        item_size[i] = m.addVar(lb=10001, ub=20000, vtype=GRB.INTEGER, name="item_size[%s]" % i)
    m.update()

    violated_constraint = {}
    for i in range(len(allowed_triplets) + len(forbidden_triplets)):
        violated_constraint[i] = m.addVar(vtype=GRB.BINARY, name="violated_constraint[%s]" % i)

    # Constraints
    for i in range(len(allowed_triplets)):
        triplet_pattern = allowed_triplets[i]
        m.addConstr(quicksum([item_size[j] * triplet_pattern[j] for j in range(len(triplet_pattern))]) - 40002 * violated_constraint[i] <= 40001,
                    name="allowed triplet size constraint")
    m.update()

    for i in range(len(forbidden_triplets)):
        triplet_pattern = forbidden_triplets[i]
        m.addConstr(quicksum([item_size[j] * triplet_pattern[j] for j in range(len(triplet_pattern))]) + 40002 * violated_constraint[i+len(allowed_triplets)] >= 40002,
                    name="forbidden triplet size constraint")
    m.update()

    m.setObjective(quicksum([violated_constraint[i] for i in range(len(violated_constraint))]), sense=GRB.MINIMIZE)
    m.update()

    return m

