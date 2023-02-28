import gurobipy as gp
from gurobipy import GRB
import operator as op

#######
# In this file, the number of items per size category is FIXED. We iterate over all feasible item size category distributions.
#######
dimension = 7
target_lp_sol = 6  # TODO: also check for lp solutions 5, 4, 3, ...
num_items = dimension * (dimension - 1)
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


def read_size_cat_dists():
    lists = []
    f = open('size_cat_dists.txt', 'r')
    lines = f.readlines()
    f.close()
    for line in lines:
        line = line.split(sep="[")[1]
        line = line.split(sep=" ]")[0]
        line = line.split(sep=" ")
        list = [int(i) for i in line]
        lists.append(list)
    return lists


patterns = pattern_finder(7)
size_cat_dists = read_size_cat_dists()

b = 0
for scd in size_cat_dists:
    print(b)
    b += 1
    target_lp_sol = 6
    while target_lp_sol > 0:
        print("#############################################################")
        print("--------------------- target_lp_sol = " + str(target_lp_sol) + "---------------------")
        print("#############################################################")
        with gp.Env() as env, gp.Model(env=env) as m, gp.Model(env=env) as m2:
            # m is the main problem
            # m2 is the problem of finding a violated inequality\
            n = scd

            for i in range(dimension):
                x = [m.addVar(vtype=GRB.BINARY,
                              name="x(" + str(pat[0]) + ", " + str(pat[1]) + ", " + str(pat[2]) + ", " + str(
                                  pat[3]) + ", " + str(
                                  pat[4]) + ", " + str(pat[5]) + ", " + str(pat[6]) + ")") for pat in
                     patterns]
            m.update()

            # s[i] is the size of an item in category i
            # In the following constraints we use big M
            s = [m.addVar(vtype=GRB.CONTINUOUS, lb=1 / 7, ub=1, name="s[%s]" % i) for i in range(dimension)]
            for p in range(len(patterns)):
                m.addConstr(gp.quicksum(s[i] * patterns[p][i] for i in range(dimension)) <= 1 + (1 - x[p]) * M)
                m.addConstr(gp.quicksum(s[i] * patterns[p][i] for i in range(dimension)) >= 1.0001 - x[p] * M)
            m.update()

            y = [m.addVar(vtype=GRB.CONTINUOUS,
                          name="y(" + str(pat[0]) + ", " + str(pat[1]) + ", " + str(pat[2]) + ", " + str(
                              pat[3]) + ", " + str(
                              pat[4]) + ", " + str(pat[5]) + ", " + str(pat[6]) + ")", lb=0)
                 for pat in patterns]
            for p in range(len(y)):
                m.addConstr(y[p] <= x[p] * dimension)
            for i in range(len(n)):
                m.addConstr(gp.quicksum([y[p] * patterns[p][i] for p in range(len(patterns))]) == n[i])
            m.addConstr(gp.quicksum(y) <= target_lp_sol)
            m.update()

            z = [m2.addVar(vtype=GRB.INTEGER, lb=0, ub=dimension,
                           name="z(" + str(pat[0]) + ", " + str(pat[1]) + ", " + str(pat[2]) + ", " + str(
                               pat[3]) + ", " + str(
                               pat[4]) + ", " + str(pat[5]) + ", " + str(pat[6]) + ")") for pat
                 in patterns]
            m2.addConstr(gp.quicksum(z) <= target_lp_sol + 1)

            m2.Params.OutputFlag = 0
            # m2.Params.Threads = 24
            m2.Params.Method = 2
            m2.update()


            def solve_ip(x_):
                '''
                Objective obj2 is maximized in order to ensure that z[p] = 1 only for patterns p that are allowed, i.e. x_[p] = 1
                :param x_: integer values of variables x from model m
                :param n_: integer values of variables n from model m
                :return:
                '''
                obj2 = gp.quicksum([z[i] * x_[i] for i in range(len(patterns))])
                m2.setObjective(obj2, GRB.MAXIMIZE)
                for i in range(len(n)):
                    m2.addConstr(gp.quicksum([z[p] * patterns[p][i] for p in range(len(patterns))]) >= n[i],
                                 name="m2coverage%s" % i)
                m2.update()
                m2.optimize()
                for i in range(len(n)):
                    c = m2.getConstrByName("m2coverage%s" % i)
                    m2.remove(c)
                sol = [pat.X for pat in z]
                val = m2.ObjVal
                return val, sol


            def callback(model, where):
                if where == GRB.Callback.MIPSOL:
                    x_ = model.cbGetSolution(x)
                    y_ = model.cbGetSolution(y)
                    sumy = gp.quicksum(y_)  # for diagnostic purposes only

                    obj, x_used = solve_ip(x_)
                    # print("obj = " + str(obj))
                    if obj <= target_lp_sol + 1.001:
                        sum = 0
                        counter = 0
                        for i in range(len(z)):
                            if x_used[i] >= 0.999:
                                sum += x[i]
                                counter += 1
                        # model.cbLazy(sum, GRB.LESS_EQUAL, counter - 1)
                        # TODO: ask Lars whether here I need to actually do -2 due to the less equal
                        # model.cbLazy(gp.quicksum([n_ik[i][n_[i] + 1] for i in range(dimension)]) >= 1)
                        model.cbLazy(sum <= counter - 1)
                        model.update()


            m.Params.LazyConstraints = 1
            m.Params.NodefileStart = 4
            m.Params.Method = 2

            m.optimize(callback)

            if m.status == GRB.OPTIMAL:
                for v in m.getVars():
                    if v.X > 0.001:
                        print('%s %g' % (v.VarName, v.X))

                print('Obj: %g' % m.ObjVal)
        target_lp_sol -= 1
