from gurobipy import GRB
import gurobipy as gp


def pattern_to_string(pattern):
	return ', '.join(str(e) for e in pattern)


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


def lp_runner(inputfilepath):
	n, x, dimension = read_allowed_patterns(inputfilepath)

	model = lp_builder(n=n,
					   allowed_patterns=x,
					   dimension=dimension)
	model.optimize()
	return model


def lp_builder(n,
			   allowed_patterns,
			   dimension):
	m = gp.Model("ILP solution finder")

	z = [m.addVar(vtype=GRB.INTEGER, lb=0, ub=dimension,
				  name="z(" + pattern_to_string(pat) + ")") for pat in allowed_patterns]
	for i in range(dimension):
		m.addConstr(gp.quicksum([z[p] * allowed_patterns[p][i] for p in range(len(allowed_patterns))]) == n[i],
					name="m2coverage%s" % i)
	m.update()

	obj2 = gp.quicksum([z[p] for p in range(len(allowed_patterns))])
	m.setObjective(obj2, GRB.MINIMIZE)
	m.update()

	return m


model = lp_runner(inputfilepath="in/instance0.txt")
if model.status == GRB.OPTIMAL:
	for v in model.getVars():
		if v.X > 0.001:
			print('%s %g' % (v.VarName, v.X))

	print('Obj: %g' % model.ObjVal)
