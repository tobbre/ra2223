import copy
import time
import gurobipy as gp
from gurobipy import GRB
import math

## In this file, the n[i] are variables.

for dim in range(15, 22):
	dimension = dim
	M = 2


	def pattern_finder(dimension, max_items_per_pattern):
		output = []
		pat = [0] * dimension
		output.append(tuple(pat.copy()))
		while (pat[0] < max_items_per_pattern):
			pointer = dimension - 1
			while sum(pat) == max_items_per_pattern:
				pat[pointer] = 0
				pointer -= 1
			pat[pointer] += 1
			output.append(tuple(pat.copy()))
		return output


	def pattern_to_string(pattern):
		return ', '.join(str(e) for e in pattern)


	patterns = pattern_finder(dimension=dimension,
	                          max_items_per_pattern=3) # Due to 3-partition instance

	if (dimension + 6) % 3 == 0:
		# since there are dimension + 6 items,
		target_lp_sol = (dimension + 6) / 3
		max_num_items = int(target_lp_sol * 3)
		start_time = time.time()
		print("#############################################################")
		print("--------------------- target_lp_sol = " + str(target_lp_sol) + "---------------------")
		print("#############################################################")
		with gp.Model("MainMIP") as m:
			# m is MainMIP

			# The n vector contains information how many items are in each of the len(n) = dimension different size categories
			# n = [m.addVar(vtype=GRB.INTEGER, name="n%s" % i, lb=0, ub=max_num_items - 1) for i in
			#      range(dimension)]
			# m.addConstr(gp.quicksum(n) == max_num_items)    # Equality, since we want exactly 3*target_lp_sol items

			n = [1] * dimension
			n[dimension - 1] = 7
			# n_ik = []
			# for i in range(dimension):
			# 	var_list = []
			# 	for k in range(max_num_items):
			# 		var_list.append(m.addVar(vtype=GRB.BINARY, name="n_%s^%s" % (i, k)))
			# 	n_ik.append(var_list)
			# m.update()
			# for i in range(dimension):
			# 	m.addConstr(n[i] == gp.quicksum([n_ik[i][k] for k in range(max_num_items)]))
			# 	for k in range(max_num_items - 1):
			# 		m.addConstr(n_ik[i][k] >= n_ik[i][k + 1])

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
				m.addConstr(s[dimension - 1] >= 1/3 + 0.00001)
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

			counters_cp = []
			counter_noSmallestOrLargest = 0
			counter_2nLargest = 0
			counter_nMinusBtriples = 0
			counter_callbackMIP = 0
			counters_cp.append(counter_noSmallestOrLargest)
			counters_cp.append(counter_2nLargest)
			counters_cp.append(counter_nMinusBtriples)
			counters_cp.append(counter_callbackMIP)

			def callback(model, where):
				if where == GRB.Callback.MIPSOL:
					x_ = model.cbGetSolution(x)
					# n_ = model.cbGetSolution(n)
					n_ = n
					s_ = model.cbGetSolution(s)
					slack = {}
					for pat in patterns:
						pat_as_list = list(pat)
						slack[pat] = 1 - sum(pat_as_list[i] * s_[i] for i in range(dimension))
						x_[pat] = round(x_[pat])
					for i in range(dimension):
						n_[i] = round(n_[i])

					# y_ = model.cbGetSolution(y)
					# sumy = gp.quicksum(y_)  # for diagnostic purposes only
					# n_ik_ = []
					# for i in range(dimension):
					# 	n_ik_.append(model.cbGetSolution(n_ik[i]))

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
							             name="m2coverage%s" % i)   # Note that == is faster than >= here.

						for pat in patterns:
							if x_[pat] == 0:
								m2.addConstr(z[pat] == 0)

						# obj2 = gp.quicksum([z[pat] for pat in patterns])
						# m2.setObjective(obj2, GRB.MINIMIZE)

						#Alternatively, we can just look for a solution that works
						m2.addConstr(gp.quicksum([z[pat] for pat in patterns]) <= target_lp_sol + 1)


						# while minimizing the Sum Of Squared Slacks (balancing)
						m2.setObjective(gp.quicksum(math.pow(slack[pat], 2) * z[pat] for pat in patterns), GRB.MINIMIZE)

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
							m3.addConstr(gp.quicksum([z[pat] * pat[i] for pat in patterns]) <= n_[i],
							             name="m2coverage%s" % i)
						# It is crucial that it's <=! NOT ==! This constraint should not make sure that every item is
						# covered, but it should make sure that no more than all items of a category are covered!
						# If not all items are covered, that is fine.

						m3.addConstr(gp.quicksum([z[pat] for pat in patterns]) == target_lp_sol - B)
						m3.addConstr(
							gp.quicksum([z[pat] * sum(pat) for pat in patterns]) == 3 * target_lp_sol - 3 * B)

						for pat in patterns:
							if x_[pat] == 0:
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

					def cp_2nLargest(x_, n__, s_, target_lp_sol):
						m4 = gp.Model("CuttingPlaneFinder2MIP")
						m4.Params.OutputFlag = 0
						m4.update()

						z = {}
						for pat in patterns:
							z[pat] = m4.addVar(vtype=GRB.INTEGER, lb=0, ub=dimension,
							                   name="z(" + pattern_to_string(list(pat)) + ")")
						m4.update()

						for i in range(dimension):
							m4.addConstr(gp.quicksum([z[pat] * pat[i] for pat in patterns]) >= n__[i],
							             name="m2coverage%s" % i)

						m4.addConstr(gp.quicksum([z[pat] for pat in patterns]) <= target_lp_sol + 1)

						for pat in patterns:
							if sum(pat) == 3 \
									or x_[pat] == 0 \
									or slack[pat] < 2 / 3:
								m4.addConstr(z[pat] == 0)

						m4.update()
						m4.optimize()

						status = m4.Status
						x_used = []
						if status == 2:
							x_used = {}
							for pat in patterns:
								x_used[pat] = z[pat].X
						return status, x_used

					def cp_noSmallestOrLargest(x_, n__, target_lp_sol, remove_small, remove_large, slack):
						m5 = gp.Model("CuttingPlaneFinder3MIP")
						m5.Params.OutputFlag = 0
						m5.update()

						z = {}
						for pat in patterns:
							z[pat] = m5.addVar(vtype=GRB.INTEGER, lb=0, ub=dimension,
							                   name="z(" + pattern_to_string(list(pat)) + ")")
						m5.update()

						for i in range(dimension):
							m5.addConstr(gp.quicksum([z[pat] * pat[i] for pat in patterns]) == n__[i],
							             name="m2coverage%s" % i)

						m5.addConstr(gp.quicksum([z[pat] for pat in patterns]) <= target_lp_sol + 1 - remove_small/3 - remove_large/2)

						for pat in patterns:
							if x_[pat] == 0:
								m5.addConstr(z[pat] == 0)
								# Also, apparently this is significantly faster than saying z[pat] <= x_[pat]. I don't know why.

						# # min-maxing the slacks
						# C = m5.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=1.1, name="maximum_slack") # even though slack can be at most 1, i'd rather be safe than sorry. And since C is being minimized anyways, allowing it to be big doesn't change anything.
						# m5.update()
						# for pat in patterns:
						# 	m5.addConstr(slack[pat] * z[pat] <= C)
						# m5.setObjective(C, GRB.MINIMIZE)

						# max-minning the slacks
						# C = m5.addVar(vtype=GRB.CONTINUOUS, lb=0, ub=1, name="minimum_slack")
						# m5.update()
						# for pat in patterns:
						# 	m5.addConstr(slack[pat] * z[pat] >= C)
						# m5.setObjective(C, GRB.MAXIMIZE)

						# Alternatively, we can minimize the Sum Of Squared Slacks
						# m5.setObjective(gp.quicksum(math.pow(slack[pat], 2) * z[pat] for pat in patterns), GRB.MINIMIZE)

						m5.update()
						m5.optimize()

						status = m5.Status
						x_used = []
						if status == 2:
							x_used = {}
							for pat in patterns:
								x_used[pat] = z[pat].X
						return status, x_used

					def use_callbackMIP_as_cuttingPlane():
						status, x_used, obj = callbackMIP(x_, n_)

						if status == 2:  # If the callback MIP has found a solution
							sum = 0
							counter = 0
							for pat in patterns:
								if x_used[pat] >= 0.99999:
									sum += x[pat]
									counter += 1
							lazy_const = model.cbLazy(sum <= counter - 1)

							# # This is the old way we did it, when n[] was still variable.
							# lazy_const = model.cbLazy(sum - gp.quicksum([n_ik[i][round(n_[i])] for i in range(dimension) if
							#                                              round(n_[i]) < max_num_items]) <= counter - 1)

							model.update()
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
						# This is only valid for the 3-partition instance.
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

							categories_with_item_decrease = 0 # mnumberOf_nonzero_covered_categories - gp.quicksum([n_ik[i][round(items_covered_per_category[i]) - 1] for i in range(dimension) if round(items_covered_per_category[i]) > 0])

							model.cbLazy(sum - categories_with_item_decrease <= counter_distinct_used_patterns - 1)
							# Above constraint ensures that either a pattern is forbidden or items from a category are removed in order to make pattern combination invalid. If n-array is fixed, the constraint will only cause a pattern to be forbidden.
							model.update()
							return True

						elif status == 3:
							# There was simply no combo of n-B patterns covering 3n-3B distinct items.
							pass
							return False

					def use_cp_2nLargest_as_cuttingPlane():
						# tests have shown that this method never produces a cp.
						# This is only valid for MIRUP, not IRUP.
						# This is only valid for the 3-partition instance.
						# This was made for instances with 3*target_lp_sol items, but also works with fewer items.
						# This is only valid if n is fixed in MainMIP, since lazy constraint does not take into account possibility of a change of n, it only takes into account forbidding patterns.
						n__ = [0] * dimension
						for i in range(dimension-1, -1, -1):
							if n_[i] + sum(n__) <= 2 * target_lp_sol:
								n__[i] = n_[i]
							else:
								n__[i] = (int) (2 * target_lp_sol - sum(n__))
								break

						status, x_used = cp_2nLargest(x_, n__, s_, target_lp_sol)
						if status == 2:
							sum1 = 0
							counter_distinct_used_patterns = 0
							for pat in patterns:
								if x_used[pat] >= 0.99999:
									sum1 += x[pat]
									counter_distinct_used_patterns += 1

							model.cbLazy(sum1 <= counter_distinct_used_patterns - 1)
							# Above constraint ensures that a pattern is forbidden.
							model.update()
							return True

						elif status == 3:
							# There was simply no combo.
							pass
							return False

					def use_cp_noSmallestOrLargest_as_cuttingPlane(remove_small, remove_large, slack):
						# This is only valid for MIRUP, not IRUP.
						# This is only valid for the 3-partition instance.
						# This is only valid if n is fixed in MainMIP, since lazy constraint does not take into account possibility of a change of n, it only takes into account forbidding patterns.

						counter = 0
						n__ = copy.deepcopy(n_)
						for i in range(dimension):
							if n_[i] + counter <= remove_small:
								n__[i] = 0
								counter += n_[i]
							else:
								n__[i] -= remove_small - counter
								break
						counter = 0
						for i in range(dimension - 1, -1, -1):
							if n_[i] + counter <= remove_large:
								n__[i] = 0
								counter += n_[i]
							else:
								n__[i] -= (remove_large - counter)
								break

						status, x_used = cp_noSmallestOrLargest(x_, n__, target_lp_sol, remove_small, remove_large, slack)
						if status == 2:
							# if sum(x_used[pat] for pat in patterns) == 0:
							# 	# i.e. if remove_small and remove_large remove all items, a solution exists with no used bins.
							# 	# This causes an error, since the lazy constraint ends up being just a boolean.
							# 	# This if statement exists to detect this case and use a different cutting planes method.
							# 	return False

							sum1 = 0
							counter_distinct_used_patterns = 0
							for pat in patterns:
								if x_used[pat] >= 0.99999:
									sum1 += x[pat]
									counter_distinct_used_patterns += 1
							# if remove_small == 3:
							# 	pat = [0]*dimension
							# 	pat[0] = 1
							# 	pat[1] = 1
							# 	pat[2] = 1
							# 	pat = tuple(pat)
							# 	sum1 += x[pat]
							# 	counter_distinct_used_patterns += 1
							# if remove_small == 6:
							# 	pat = [0] * dimension
							# 	pat[0] = 1
							# 	pat[1] = 1
							# 	pat[2] = 1
							# 	pat = tuple(pat)
							# 	sum1 += x[pat]
							# 	counter_distinct_used_patterns += 1
							# 	pat = [0] * dimension
							# 	pat[3] = 1
							# 	pat[4] = 1
							# 	pat[5] = 1
							# 	pat = tuple(pat)
							# 	sum1 += x[pat]
							# 	counter_distinct_used_patterns += 1

							model.cbLazy(sum1 <= counter_distinct_used_patterns - 1)
							# Above constraint ensures that a pattern is forbidden.
							model.update()
							return True

						elif status == 3:
							# There was simply no combo.
							pass
							return False

					def isCuttingPlaneNotYetFound():
						# if use_cp_2nLargest_as_cuttingPlane():
						# 	counters_cp[1] += 1
						# 	return False
						for i in range((int) (3 * target_lp_sol - 12), -1, -3):
							if use_cp_noSmallestOrLargest_as_cuttingPlane(remove_small=i, remove_large=6, slack=slack):
								counters_cp[0] += 1
								return False
						# if use_cp_nMinusBtriples_as_cuttingPlane(2):
						# 	counters_cp[2] += 1
						# 	return False
						return True

					if isCuttingPlaneNotYetFound():
						use_callbackMIP_as_cuttingPlane()
						counters_cp[3] += 1

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
			print("\nCustom cutting planes used:")
			print("noSmallestOrLargest: " + str(counters_cp[0]))
			print("2nLargest: " + str(counters_cp[1]))
			print("nMinusBtriples: " + str(counters_cp[2]))
			print("callbackMIP: " + str(counters_cp[3]) + "\n")

			print("RT: " + str(end_time - start_time) + " seconds.")
		target_lp_sol -= 1
