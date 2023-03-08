from gurobipy import Model, quicksum, GRB, setParam
import gurobipy as gp
import numpy as np

M = 1000


def pattern_finder(dimension):
    max_number = dimension - 1
    output = []
    pat = [0] * dimension
    output.append(pat.copy())
    while (pat[0] < max_number):
        pointer = dimension - 1
        while sum(pat) == max_number:
            pat[pointer] = 0
            pointer -= 1
        pat[pointer] += 1
        output.append(pat.copy())
    return output


def lp_runner():
    dimension = 4
    patterns = pattern_finder(dimension)
    isAllowed = [0] * len(patterns)
    # So far, I have to hard code the allowed patterns.
    # TODO: If needed, write method that reads allowed patterns from file.
    for i in range(dimension):
        if (patterns[i][0] == 0 and
            patterns[i][1] == 0 and
            patterns[i][2] == 0 and
            patterns[i][3] == 2
        ) or (patterns[i][0] == 0 and
            patterns[i][1] == 0 and
            patterns[i][2] == 1 and
            patterns[i][3] == 1
        ) or (patterns[i][0] == 0 and
            patterns[i][1] == 0 and
            patterns[i][2] == 2 and
            patterns[i][3] == 1
        ) or (patterns[i][0] == 0 and
            patterns[i][1] == 1 and
            patterns[i][2] == 0 and
            patterns[i][3] == 1
        ) or (patterns[i][0] == 0 and
            patterns[i][1] == 1 and
            patterns[i][2] == 0 and
            patterns[i][3] == 2
        ) or (patterns[i][0] == 0 and
            patterns[i][1] == 1 and
            patterns[i][2] == 2 and
            patterns[i][3] == 0
        ) or (patterns[i][0] == 0 and
            patterns[i][1] == 2 and
            patterns[i][2] == 0 and
            patterns[i][3] == 0
        ) or (patterns[i][0] == 2 and
            patterns[i][1] == 1 and
            patterns[i][2] == 0 and
            patterns[i][3] == 0
        ):
                isAllowed[i] = 1

    model = lp_builder(patterns=patterns,
                       isAllowed=isAllowed,
                       dimension=dimension)
    model.optimize()
    return model


def lp_builder(patterns,
               isAllowed,
               dimension):
    m = Model("Size Category Distribution Finder")
    s = [m.addVar(vtype=GRB.CONTINUOUS, lb=(1 / dimension + 0.0001), ub=1, name="s[%s]" % i) for i in range(dimension)]
    for p in range(len(patterns)):
        m.addConstr(gp.quicksum(s[i] * patterns[p][i] for i in range(dimension)) <= 1 + (1 - isAllowed[p]) * M)
        m.addConstr(gp.quicksum(s[i] * patterns[p][i] for i in range(dimension)) >= 1.0001 - isAllowed[p] * M)
    m.update()

    return m


model = lp_runner()
if model.status == GRB.OPTIMAL:
    for v in model.getVars():
        if v.X > 0.001:
            print('%s %g' % (v.VarName, v.X))

    print('Obj: %g' % model.ObjVal)
