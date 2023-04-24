from gurobipy import Model, quicksum, GRB, setParam
import gurobipy as gp
import numpy as np

M = 1000


def pattern_finder(dimension):
    max_number = dimension - 1
    output = []
    pat = [0] * dimension
    output.append(tuple(pat.copy()))
    while (pat[0] < max_number):
        pointer = dimension - 1
        while sum(pat) == max_number:
            pat[pointer] = 0
            pointer -= 1
        pat[pointer] += 1
        output.append(tuple(pat.copy()))
    return output


def read_allowed_patterns(filepath):
    """
    The files this method can read only have information about n, x, s and y, in that order.
    In this format:
    n0 1
    n1 2
    x(0, 0, 0, 0) 1
    s[0] 0.166767
    y(0, 0, 2, 0) 2.5

    :param filepath:
    :return:
    """
    with open(filepath, "r") as f:
        lines = f.readlines()
        n_start = 0
        x_start = 0
        s_start = 0
        for i in range(len(lines)):
            if lines[i][0] == "x":
                x_start = i
                break
        dimension = int(lines[x_start-1].split(" ")[0].split("n")[1]) + 1
        for i in range(x_start, len(lines)):
            if lines[i][0] == "s":
                s_start = i
                break
        n = [0]*dimension
        for i in range(n_start, x_start):
            item = int(lines[i].split(" ")[0].split("n")[1])
            n[item] = int(lines[i].split("\n")[0].split(" ")[1])
        x = [lines[i].split("(")[1].split(")")[0].split(", ")[:] for i in range(x_start, s_start)]
        for i in range(len(x)):
            for j in range(len(x[0])):
                x[i][j] = int(x[i][j])
        return n, x, dimension


def lp_runner(filepath):
    n, x, dimension = read_allowed_patterns(filepath=filepath)
    patterns = pattern_finder(dimension)
    isAllowed = [0] * len(patterns)
    # So far, I have to hard code the allowed patterns.
    for pattern in x:
        isAllowed[patterns.index(tuple(pattern))] = 1

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
    m.update()
    for p in range(len(patterns)):
        m.addConstr(gp.quicksum(s[i] * patterns[p][i] for i in range(dimension)) <= 1 + (1 - isAllowed[p]) * M)
        if sum(list(patterns[p])) != 1:
            m.addConstr(gp.quicksum(s[i] * patterns[p][i] for i in range(dimension)) >= 1.00001 - isAllowed[p] * M)
    m.update()

    return m


model = lp_runner(filepath="in/instance0.txt")
if model.status == GRB.OPTIMAL:
    for v in model.getVars():
        if v.X > 0.001:
            print('%s %g' % (v.VarName, v.X))

    print('Obj: %g' % model.ObjVal)
