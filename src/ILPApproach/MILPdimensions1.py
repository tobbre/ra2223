import time
import gurobipy as gp
from gurobipy import GRB

#######
# In this file, the number of items per size category is a VARIABLE.
#######
dimension = 5
target_lp_sol = dimension # TODO: CHANGE THIS BACK TO dimension
# num_items = dimension * (dimension - 1) # outdated, I found a better bound
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
    num_items = target_lp_sol * (dimension - 1) + (target_lp_sol - 1)
    start_time = time.time()
    print("#############################################################")
    print("--------------------- target_lp_sol = " + str(target_lp_sol) + "---------------------")
    print("#############################################################")
    with gp.Model("MainMIP") as m:
        # m is MainMIP

        # The n vector contains information how many items are in each of the len(n) different size categories
        n = [m.addVar(vtype=GRB.INTEGER, name="n%s" % i, lb=0, ub=num_items - 1) for i in
             range(dimension)]
        m.addConstr(gp.quicksum(n) <= num_items)

        n_ik = []
        for i in range(dimension):
            var_list = []
            for k in range(num_items):
                var_list.append(m.addVar(vtype=GRB.BINARY, name="n_%s^%s" % (i, k)))
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
        s = [m.addVar(vtype=GRB.CONTINUOUS, lb=(1/dimension + 0.00001), ub=1, name="s[%s]" % i) for i in range(dimension)]
        for p in range(len(patterns)):
            m.addConstr(gp.quicksum(s[i] * patterns[p][i] for i in range(dimension)) <= 1 + (1 - x[p]) * M, name="size_consistent_allowed")
            m.addConstr(gp.quicksum(s[i] * patterns[p][i] for i in range(dimension)) >= 1.00001 - x[p] * M, name="size_consistent_forbidden")
        for i in range(dimension - 1):
            # m.addConstr(s[i] <= s[i+1])   # Including this constraint instead results in significantly higher running times.
            m.addConstr(n[i] <= n[i+1])
        m.update()

        y = [m.addVar(vtype=GRB.CONTINUOUS,
                      name="y(" + pattern_to_string(pat) + ")", lb=0, ub=dimension)
             for pat in patterns]
        for p in range(len(patterns)):
            m.addConstr(y[p] <= x[p] * dimension, name="usage")
        for i in range(len(n)):
            m.addConstr(gp.quicksum([y[p] * patterns[p][i] for p in range(len(patterns))]) == n[i], name="coverage")
        m.addConstr(gp.quicksum(y) <= target_lp_sol, name="lp_value_constraint")
        m.update()




        def callbackMIP(x_, n_):
            '''
            Finds optimal integer solution to instance with allowed patterns and item quantities according to x_ and n_ respectively.
            :param x_: integral values of variables x from model m
            :param n_: integral values of variables n from model m
            :return:
            '''
            m2 = gp.Model("CallbackMIP")
            m2.Params.OutputFlag = 0
            m2.update()

            z = [m2.addVar(vtype=GRB.INTEGER, lb=0, ub=dimension,
                           name="z(" + pattern_to_string(pat) + ")") for pat in patterns]
            for i in range(dimension):
                m2.addConstr(gp.quicksum([z[p] * patterns[p][i] for p in range(len(patterns))]) >= n_[i],
                             name="m2coverage%s" % i)
            m2.update()
            for p in range(len(patterns)):
                m2.addConstr(z[p] <= x_[p] * (dimension+1))
            m2.update()

            obj2 = gp.quicksum([z[p] for p in range(len(patterns))])
            m2.setObjective(obj2, GRB.MINIMIZE)
            m2.optimize()

            status = m2.Status
            x_used = []
            obj = -1
            if status == 2:
                x_used = [v.X for v in z]
                obj = m2.ObjVal

                # TODO: REMOVE THE CODE BELOW IN THIS IF STATEMENT
                if obj == target_lp_sol + 2:
                    allowed = [patterns[i] for i in range(len(patterns)) if x_[i] == 1]
                    print("allowed patters for CallbackMIP:")
                    for i in range(len(allowed)):
                        print(allowed[i])
                    print("n:")
                    print(n_)
                    for v in m2.getVars():
                        if v.X > 0.001:
                            print('%s %g' % (v.VarName, v.X))
                    print('Obj: %g' % m2.ObjVal + "\n\n\n")
            if status == 3:
                pass
            return status, x_used, obj


        def callback(model, where):
            if where == GRB.Callback.MIPSOL:
                x_ = model.cbGetSolution(x)
                x_ = [round(x_[p]) for p in range(len(x_))]
                n_ = model.cbGetSolution(n)

                y_ = model.cbGetSolution(y)
                sumy = gp.quicksum(y_)  # for diagnostic purposes only
                n_ik_ = []
                for i in range(dimension):
                    n_ik_.append(model.cbGetSolution(n_ik[i]))

                status, x_used, obj = callbackMIP(x_, n_)

                if status == 2: # If the callback MIP has found a solution
                    if obj <= target_lp_sol + 1.00001:
                        sum = 0
                        counter = 0
                        for i in range(len(x_used)):
                            if x_used[i] >= 0.99999:
                                sum += x[i]
                                counter += 1
                        added_constraint = model.cbLazy(sum - gp.quicksum([n_ik[i][round(n_[i])] for i in range(dimension) if round(n_[i]) < num_items]) <= counter - 1)
                        # Above constraint ensures that either a pattern is forbidden or an item is increased in number.
                        model.update()
                    else:
                        print("CallbackMIP is feasible, but ILP objective value is " + str(obj) + "!")
                elif status == 3:
                    print("Callback MIP is infeasible.")
                    pass


        m.Params.LazyConstraints = 1
        m.Params.NodefileStart = 4

        m.optimize(callback)

        if m.status == GRB.OPTIMAL:
            for v in m.getVars():
                if v.X > 0.001:
                    print('%s %g' % (v.VarName, v.X))

            print('Obj: %g' % m.ObjVal)
        end_time = time.time()
        print("RT: " + str(end_time - start_time) + " seconds.")
    target_lp_sol -= 1
