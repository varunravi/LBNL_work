

with open('base_env.txt', 'r') as file:
	lines = file.readlines()
for line in lines:
	for i, let in reversed(list(enumerate(line))):
		if let == '=':
			print('- {}'.format(line[:i]))
			break
