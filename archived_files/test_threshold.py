
pruning = {
            40 : 1.5,
            60: 4,
            80: 8,
            90: 10,
            100: 15,
            120: 25,
            130: 35,

        }

current_gen_threshold = 0
g = 61
for gen_nr in pruning.keys():
    if gen_nr > g:
        break
    current_gen_threshold = gen_nr

print(current_gen_threshold)
    