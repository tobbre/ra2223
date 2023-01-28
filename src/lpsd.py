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


def sd_n_binding_constr(binding_constraints, index_first_forbidden):
    '''
    Calucaltes the size distribution using matrix inversion based on a total of n allowed or forbidden patterns
    :param binding_constraints: a 2D array containing the n patterns of the binding constraints in bit format
    :param index_first_forbidden: the index of the first forbidden pattern in binding_constraints
    :return: item size distribution if it exists, -1 if it does not exist. sd = binding_constraints^-1 * b
    '''
    n = len(binding_constraints)
    b = [1] * index_first_forbidden + [1.001] * (n - index_first_forbidden)
    if np.linalg.det(binding_constraints) != 0:
        inverse = np.linalg.inv(binding_constraints)
        sd = inverse.dot(b)
        return sd
    else:
        return -1
