all_lines = []
sorted_lines = []

with open("rez_generation_0", 'r') as r:
    
    for line in r.readlines():
        all_lines.append(line)
    sorted_lines = sorted(all_lines, key = lambda x: float(x.split("|")[0]))

with open("rez_generation_0_s", 'w') as w:
    for line in sorted_lines:
        w.write(line)