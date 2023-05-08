import time
import gurobipy as gp
from gurobipy import GRB

## In this file, the n[i] are parameters.


dimension = 9
target_lp_sol = dimension
M = dimension + 1


def pattern_finder(dimension, max_number):
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


def size_cat_dist_finder(dimension, max_number):
	# Here we assume that n is non-decreasing, i.e. n[0]<=n[1]<=...
	output = []
	pat = [0] * dimension
	while (pat[0] < max_number):
		pointer = dimension - 1
		while sum(pat) == max_number:
			pat[pointer] = 0
			pointer -= 1
		pat[pointer] += 1
		order_checker_array = [not(pat[i] == pat[i+1]) for i in range(dimension-1)]
		if sum(order_checker_array) == 0:
			output.append(tuple(pat.copy()))
	return output


def pattern_to_string(pattern):
	return ', '.join(str(e) for e in pattern)


patterns = pattern_finder(dimension=dimension, max_number=3)    # Due to 3-partition instance


while target_lp_sol > 1:
	max_num_items = target_lp_sol * 3 - 2  # Due to 3-partition instance
	# size_cat_dists = size_cat_dist_finder(dimension=dimension,
	#                                 max_number=max_num_items)
	size_cat_dists = [(2,2,2,2,2,2,2,2,2), (1,1,1,1,1,1,1,1,1)]
	start_time = time.time()
	print("#############################################################")
	print("--------------------- target_lp_sol = " + str(target_lp_sol) + "---------------------")
	print("#############################################################")

	# The n vector contains information how many items are in each of the len(n) = dimension different size categories
	for i in range(len(size_cat_dists)):
		n = size_cat_dists[i]
		print("\n\nsize_cat_dist: " + str(n))
		with gp.Model("MainMIP") as m:
			# m is MainMIP

			x = {}
			for pat in patterns:
				x[pat] = m.addVar(vtype=GRB.BINARY, name="x(" + pattern_to_string(list(pat)) + ")")
			m.update()
			m.addConstr(x[patterns[0]] == 1)  # This ensures that pattern (0,0,...,0) is allowed

			# Due to 3-partition instance
			# Probably only small impact, because maximum item size of 0.5 implies via constraints below that all
			# single and double patterns must be allowed. But still good to have.
			for pat in patterns:
				if sum(pat) != 3:
					m.addConstr(x[pat] == 1)


			keys = list(x)
			for key_as_tuple in keys:
				key_as_array = list(key_as_tuple)
				for i in range(dimension):
					if key_as_array[i] != 0:
						key_as_array[i] -= 1
						m.addConstr(x[key_as_tuple] <= x[tuple(key_as_array)])
						key_as_array[i] += 1


			def s_order_constraints():
				for i in range(dimension - 1):
					m.addConstr(s[i] <= s[i + 1])
				for key_as_tuple in keys:
					key_as_array = list(key_as_tuple)
					for i in range(1, dimension):
						if key_as_array[i] != 0 and key_as_array[i - 1] != dimension - 1:
							key_as_array[i] -= 1
							key_as_array[i - 1] += 1
							m.addConstr(x[key_as_tuple] <= x[tuple(key_as_array)])
							key_as_array[i - 1] -= 1
							key_as_array[i] += 1
				m.update()


			# s[i] is the size of an item in category i
			s = [m.addVar(vtype=GRB.CONTINUOUS, lb=0.25 + 0.00001, ub=0.5 - 0.00001, name="s[%s]" % i) for i in
			     range(dimension)]  # Due to 3-partition instance
			m.update()
			# Allowed patterns and forbidden patterns must satisfy the following
			for pat in patterns:
				m.addConstr(gp.quicksum(s[i] * pat[i] for i in range(dimension)) <= 1 + (1 - x[pat]) * M)
				if sum(list(pat)) != 1:
					m.addConstr(gp.quicksum(s[i] * pat[i] for i in range(dimension)) >= 1.00001 - x[pat] * M)

			# s_order_constraints()

			y = {}
			for pat in patterns:
				y[pat] = m.addVar(vtype=GRB.CONTINUOUS, name="y(" + pattern_to_string(list(pat)) + ")", lb=0, ub=1)
			m.update()
			for pat in patterns:
				m.addConstr(y[pat] <= x[pat], name="usage")
			for i in range(len(n)):
				m.addConstr(gp.quicksum([y[pat] * pat[i] for pat in patterns]) == n[i], name="coverage")

			m.addConstr(gp.quicksum([y[pat] for pat in patterns]) <= target_lp_sol, name="lp_value_constraint")
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
				# m2.Params.Threads = 24
				m2.update()

				z = {}
				for pat in patterns:
					z[pat] = m2.addVar(vtype=GRB.INTEGER, lb=0, ub=dimension,
					                   name="z(" + pattern_to_string(list(pat)) + ")")
				m2.update()

				for i in range(dimension):
					m2.addConstr(gp.quicksum([z[pat] * pat[i] for pat in patterns]) == n_[i],
					             name="m2coverage%s" % i)

				for pat in patterns:
					m2.addConstr(z[pat] <= x_[pat] * dimension)

				obj2 = gp.quicksum([z[pat] for pat in patterns])
				m2.setObjective(obj2, GRB.MINIMIZE)
				m2.update()
				m2.optimize()

				status = m2.Status
				x_used = []
				obj = -1
				if status == 2:
					x_used = {}
					for pat in patterns:
						x_used[pat] = z[pat].X
					obj = m2.getObjective().getValue()

				# The code below outputs the list of allowed patterns in a found solution.
				# if obj >= target_lp_sol + 1:
				# 	print("Allowed patterns:")
				# 	for pat in patterns:
				# 		if x_[pat] >= 0.9:
				# 			print(str(pat) + " " + str(x_[pat]))
				# 	print("Used patterns:")
				# 	for pat in patterns:
				# 		if x_used[pat] >= 0.99999:
				# 			print(str(pat) + " " + str(x_used[pat]))

				if status == 3:
					pass
				return status, x_used, obj


			def callback(model, where):
				if where == GRB.Callback.MIPSOL:
					x_ = model.cbGetSolution(x)
					n_ = n
					for pat in patterns:
						x_[pat] = round(x_[pat])

					y_ = model.cbGetSolution(y)
					sumy = gp.quicksum(y_)  # for diagnostic purposes only

					status, x_used, obj = callbackMIP(x_, n_)

					if status == 2:  # If the callback MIP has found a solution
						if obj <= target_lp_sol + 1.00001:
							sum = 0
							counter = 0
							for pat in patterns:
								if x_used[pat] >= 0.99999:
									sum += x[pat]
									counter += 1
							lazy_const = model.cbLazy(sum <= counter - 1)
							# Above constraint ensures that a pattern is forbidden.
							model.update()
						else:
							print("CallbackMIP is feasible, but ILP objective value is " + str(obj) + "!")
						# print("Allowed patterns:")
						# for pat in patterns:
						# 	if x_[pat] >= 0.9:
						# 		print(str(pat) + " " + str(x_[pat]))
						# print("Used patterns:")
						# for pat in patterns:
						# 	if x_used[pat] >= 0.99999:
						# 		print(str(pat) + " " + str(x_used[pat]))
					elif status == 3:
						print("Callback MIP is infeasible.")
						pass


			m.Params.LazyConstraints = 1
			m.Params.CutPasses = 1
			m.Params.NodefileStart = 4
			m.Params.IntFeasTol = 1e-09

			m.optimize(callback)

			if m.status == GRB.OPTIMAL:
				for v in m.getVars():
					if v.X > 0.001:
						print('%s %g' % (v.VarName, v.X))

				print('Obj: %g' % m.ObjVal)
			if i % 1000 == 0:
				end_time = time.time()
				print("RT for " + i + " size_cat_dists: " + str(end_time - start_time) + " seconds.")
	target_lp_sol -= 1
