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

dim = 7
a = pattern_finder(dim)
pass