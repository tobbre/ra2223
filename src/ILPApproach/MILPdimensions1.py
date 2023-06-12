import copy
import time
import gurobipy as gp
from gurobipy import GRB

## In this file, the n[i] are variables.


dimension = 20
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


def pattern_to_string(pattern):
	return ', '.join(str(e) for e in pattern)


patterns = pattern_finder(dimension=dimension,
                          max_number=3) # Due to 3-partition instance

while target_lp_sol > 1:
	max_num_items = target_lp_sol * 3
	start_time = time.time()
	print("#############################################################")
	print("--------------------- target_lp_sol = " + str(target_lp_sol) + "---------------------")
	print("#############################################################")
	with gp.Model("MainMIP") as m:
		# m is MainMIP

		# The n vector contains information how many items are in each of the len(n) = dimension different size categories
		n = [1] * dimension   # Since we want exactly 1 items per category. This is the general case again, with dimension-many items.
		n[dimension - 1] = 6
		n_ik = []
		for i in range(dimension):
			var_list = []
			for k in range(max_num_items):
				var_list.append(m.addVar(vtype=GRB.BINARY, name="n_%s^%s" % (i, k)))
			n_ik.append(var_list)
		m.update()
		for i in range(dimension):
			m.addConstr(n[i] == gp.quicksum([n_ik[i][k] for k in range(max_num_items)]))
			for k in range(max_num_items - 1):
				m.addConstr(n_ik[i][k] >= n_ik[i][k + 1])

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

		# # This constraint ensures that no allowed pattern contains more items than there exist in a category
		# # In the following constraints we use big M
		# # WE DO NOT USE THIS CONSTRAINT ANYMORE SINCE WE ARE NOW CONSIDERING THE UNBOUNDED CASE! SO THERE CAN BE MORE ITEMS COVERED THAN EXIST IN A CATEGORY
		# for pat in patterns:
		# 	for i in range(dimension):
		# 		m.addConstr(n[i] - pat[i] >= 0 - (1 - x[pat]) * M)

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


		def n_order_constraints():
			for i in range(dimension - 1):
				m.addConstr(n[i] <= n[i + 1])
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

		# n_order_constraints()
		s_order_constraints()

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


		def cp_nMinusBtriples(x_, n_, target_lp_sol, B):
			m3 = gp.Model("CuttingPlaneFinder1MIP")
			m3.Params.OutputFlag = 0
			m3.update()

			z = {}
			for pat in patterns:
				z[pat] = m3.addVar(vtype=GRB.INTEGER, lb=0, ub=dimension,
				                   name="z(" + pattern_to_string(list(pat)) + ")")
			m3.update()

			for i in range(dimension):
				m3.addConstr(gp.quicksum([z[pat] * pat[i] for pat in patterns]) <= n_[i], name="m2coverage%s" % i)

			m3.addConstr(gp.quicksum([z[pat] for pat in patterns]) == target_lp_sol - B)
			m3.addConstr(gp.quicksum([z[pat] * sum(pat) for pat in patterns]) == 3 * target_lp_sol - 3 * B)

			for pat in patterns:
				if sum(pat) != 3 or x_[pat] == 0:
					m3.addConstr(z[pat] == 0)

			m3.update()
			m3.optimize()

			status = m3.Status
			x_used = []
			if status == 2:
				x_used = {}
				for pat in patterns:
					x_used[pat] = z[pat].X
			return status, x_used


		def callback(model, where):
			if where == GRB.Callback.MIPSOL:
				x_ = model.cbGetSolution(x)
				# n_ = model.cbGetSolution(n)
				n_ = n
				for pat in patterns:
					x_[pat] = round(x_[pat])
				for i in range(dimension):
					n_[i] = round(n_[i])

				y_ = model.cbGetSolution(y)
				sumy = gp.quicksum(y_)  # for diagnostic purposes only
				n_ik_ = []
				for i in range(dimension):
					n_ik_.append(model.cbGetSolution(n_ik[i]))

				def use_callbackMIP_as_cuttingPlane():
					status, x_used, obj = callbackMIP(x_, n_)

					if status == 2:  # If the callback MIP has found a solution
						if obj <= target_lp_sol + 1.00001:
							sum = 0
							counter = 0
							for pat in patterns:
								if x_used[pat] >= 0.99999:
									sum += x[pat]
									counter += 1
							lazy_const = model.cbLazy(sum - gp.quicksum([n_ik[i][round(n_[i])] for i in range(dimension) if
							                                              round(n_[i]) < max_num_items]) <= counter - 1)
							# Above constraint ensures that either a pattern is forbidden or an item is increased in number.
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

				def use_cp_nMinusBtriples_as_cuttingPlane(B):
					# This is only valid for MIRUP, not IRUP.
					# It is also only valid
					status, x_used = cp_nMinusBtriples(x_, n_, target_lp_sol, B)
					if status == 2:
						sum = 0
						counter_distinct_used_patterns = 0
						items_covered_per_category = [0] * dimension
						for pat in patterns:
							if x_used[pat] >= 0.99999:
								sum += x[pat]
								counter_distinct_used_patterns += 1
								for i in range(dimension):
									items_covered_per_category[i] += pat[i] * x_used[pat]
						numberOf_nonzero_covered_categories = gp.quicksum([1 for i in range(dimension) if round(items_covered_per_category[i]) > 0])

						categories_with_item_decrease = numberOf_nonzero_covered_categories - gp.quicksum([n_ik[i][round(items_covered_per_category[i]) - 1] for i in range(dimension) if round(items_covered_per_category[i]) > 0])

						model.cbLazy(sum - categories_with_item_decrease <= counter_distinct_used_patterns - 1)
						model.update()
						return True

					elif status == 3:
						# There was simply no combo of n-B patterns covering 3n-3B distinct items.
						pass
						return False

				def isCuttingPlaneNotYetFound(B):
					return not use_cp_nMinusBtriples_as_cuttingPlane(B)

				if isCuttingPlaneNotYetFound(2):
					use_callbackMIP_as_cuttingPlane()

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
		end_time = time.time()
		print("RT: " + str(end_time - start_time) + " seconds.")
	target_lp_sol -= 1
