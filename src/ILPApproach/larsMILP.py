import gurobipy as gp
from gurobipy import GRB
import itertools as it

n = 30

with gp.Env() as env, gp.Model(env=env) as m, gp.Model(env=env) as m2:
    # m is the main problem
    # m2 is the problem of finding a violated inequality
    patterns = [pat for pat in it.combinations(range(n), 3)]
    p = [m.addVar(vtype=GRB.BINARY, name="p(" + str(pat[0]) + ", " + str(pat[1]) + ", " + str(pat[2]) + ")") for pat in
         patterns]
    p_lp = [m.addVar(vtype=GRB.CONTINUOUS, name="p_lp(" + str(pat[0]) + ", " + str(pat[1]) + ", " + str(pat[2]) + ")")
            for pat in patterns]

    p2 = [m2.addVar(vtype=GRB.BINARY, name="p2(" + str(pat[0]) + ", " + str(pat[1]) + ", " + str(pat[2]) + ")") for pat
          in patterns]
    for i in range(n):
        ni = 0
        for j in range(len(patterns)):
            if i in patterns[j]:
                ni = ni + p2[j]
        m2.addConstr(ni >= 1)
    sum = 0
    for pat in p2:
        sum = sum + pat
    m2.addConstr(sum <= n / 3 + 1)
    m2.Params.OutputFlag = 0
    #  m2.Params.Threads = 24
    m2.Params.Method = 2


    def solve_ip(p_):
        # find pattern solution <= n/3 +1 while maximizing their p_ value
        # it doesn't check for ilp solutions with exactly n/3 tripels currenctly, which I think needs to be added, but
        # does not appear to create a problem.
        obj2 = 0
        for i in range(len(patterns)):
            obj2 = obj2 + p_[i] * p2[i]
        m2.setObjective(obj2, GRB.MAXIMIZE)
        m2.optimize()
        sol = [pat.X for pat in p2]
        val = m2.ObjVal
        return val, sol


    def callback(model, where):
        if where == GRB.Callback.MIPSOL:
            p_ = model.cbGetSolution(p)
            obj, p_used = solve_ip(p_)
            if obj > n / 3 + 0.001:
                sum = 0
                for i in range(len(patterns)):
                    if p_used[i] >= 0.999:
                        sum = sum + p[i]
                model.cbLazy(sum <= n / 3)


    for i in range(n):
        ni = 0
        for j in range(len(patterns)):
            for el in patterns[j]:
                if el <= i:
                    ni = ni + p_lp[j]
        m.addConstr(ni >= i + 1)

    for i in range(len(patterns)):
        pat = patterns[i]
        m.addConstr(p_lp[i] <= n * p[i])
        m.addConstr(p_lp[i] >= 0)

    prev0 = [[None for i in range(n)] for j in range(n)]
    prev1 = [[None for i in range(n)] for j in range(n)]
    prev2 = [[None for i in range(n)] for j in range(n)]
    for i in range(len(patterns) - 1):
        pat = patterns[i]
        if prev0[pat[1]][pat[2]] is not None:
            m.addConstr(p[prev0[pat[1]][pat[2]]] <= p[i])
        prev0[pat[1]][pat[2]] = i

        if prev1[pat[0]][pat[2]] is not None:
            m.addConstr(p[prev1[pat[0]][pat[2]]] <= p[i])
        prev1[pat[0]][pat[2]] = i

        if prev2[pat[0]][pat[1]] is not None:
            m.addConstr(p[prev2[pat[0]][pat[1]]] <= p[i])
        prev2[pat[0]][pat[1]] = i
    del prev0
    del prev1
    del prev2

    lp_opt = 0
    for pat in p_lp:
        lp_opt = lp_opt + pat
    m.setObjective(lp_opt, GRB.MINIMIZE)

    m.Params.LazyConstraints = 1
    m.Params.NodefileStart = 4
    m.Params.Method = 2
    m.Params.Cutoff = n / 3 + 0.001
    #  m.Params.SolutionLimit = 1

    m.optimize(callback)

    if m.status == GRB.OPTIMAL:
        for v in m.getVars():
            if v.X > 0.001:
                print('%s %g' % (v.VarName, v.X))

        print('Obj: %g' % m.ObjVal)
