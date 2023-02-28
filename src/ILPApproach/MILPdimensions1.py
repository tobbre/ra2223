import gurobipy as gp
from gurobipy import GRB
import operator as op

#######
# In this file, the number of items per size category is a VARIABLE.
#######
dimension = 5
target_lp_sol = dimension - 1  # TODO: also check for lp solutions for dim - 2, dim - 3, ...
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


def pattern_to_string(pattern):
    return ', '.join(str(e) for e in pattern)


patterns = pattern_finder(dimension)

while target_lp_sol > 0:
    print("#############################################################")
    print("--------------------- target_lp_sol = " + str(target_lp_sol) + "---------------------")
    print("#############################################################")
    with gp.Env() as env, gp.Model(env=env) as m, gp.Model(env=env) as m2:
        # m is the main problem
        # m2 is the problem of finding a violated inequality

        # The n vector contains information how many items are in each of the len(n) different size categories
        n = [m.addVar(vtype=GRB.INTEGER, name="n%s" % i, lb=0, ub=dimension * (dimension - 1)) for i in
             range(dimension)]

        # n_ik[i][k] = 1 iff n[i] >= k + 1  (the definition in the mathematical formulation is a tiny bit different, since there we start counting at 1 but python starts counting at 0)
        n_ik = []
        for i in range(dimension):
            var_list = []
            for k in range(num_items):
                var_list.append(m.addVar(vtype=GRB.BINARY, name="n_%s^%s" % (i, k + 1)))
            n_ik.append(var_list)
        m.update()
        for i in range(dimension):
            m.addConstr(n[i] == gp.quicksum([n_ik[i][k] for k in range(num_items)]))
            for k in range(num_items - 1):
                m.addConstr(n_ik[i][k] >= n_ik[i][k + 1])
        m.update()

        x = [m.addVar(vtype=GRB.BINARY,
                      name="x(" + pattern_to_string(pat) + ")") for pat in
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
                      name="y(" + pattern_to_string(pat) + ")", lb=0)
             for pat in patterns]
        for p in range(len(y)):
            m.addConstr(y[p] <= x[p] * dimension)
        for i in range(len(n)):
            m.addConstr(gp.quicksum([y[p] * patterns[p][i] for p in range(len(patterns))]) == n[i])
        m.addConstr(gp.quicksum(y) <= target_lp_sol)
        m.update()

        z = [m2.addVar(vtype=GRB.INTEGER, lb=0, ub=dimension,
                       name="z(" + pattern_to_string(pat) + ")") for pat
             in patterns]
        m2.addConstr(gp.quicksum(z) <= target_lp_sol + 1)

        m2.Params.OutputFlag = 0
        # m2.Params.Threads = 24
        m2.Params.Method = 2
        m2.update()


        def solve_ip(x_, n_):
            '''
            Objective obj2 is maximized in order to ensure that z[p] = 1 only for patterns p that are allowed, i.e. x_[p] = 1
            :param x_: integer values of variables x from model m
            :param n_: integer values of variables n from model m
            :return:
            '''
            obj2 = gp.quicksum([z[i] * x_[i] for i in range(len(patterns))])
            m2.setObjective(obj2, GRB.MAXIMIZE)
            for i in range(len(n)):
                m2.addConstr(gp.quicksum([z[p] * patterns[p][i] for p in range(len(patterns))]) >= n_[i],
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
                n_ = model.cbGetSolution(n)
                n_ik_ = []
                for i in range(dimension):
                    n_ik_.append(model.cbGetSolution(n_ik[i]))

                obj, x_used = solve_ip(x_, n_)
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
                    model.cbLazy(sum - gp.quicksum([n_ik[i][round(n_[i])] for i in range(dimension)]) <= counter - 1)
                    # Above constraint ensures that either a pattern is forbidden or an item is increased in number.
                    # since n_ik[i][k] = 1 iff n_i >= k + 1 (this is since python starts indexing at 0), having k = n[i] forces some item to increase.
                    model.update()


        m.Params.LazyConstraints = 1
        m.Params.NodefileStart = 4
        m.Params.Method = 2  # TODO: set this to -1, automatic. Maybe then it's faster

        m.optimize(callback)

        if m.status == GRB.OPTIMAL:
            for v in m.getVars():
                if v.X > 0.001:
                    print('%s %g' % (v.VarName, v.X))

            print('Obj: %g' % m.ObjVal)
    target_lp_sol -= 1
