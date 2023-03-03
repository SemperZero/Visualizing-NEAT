import sys
sys.path.insert(0, '')
from evo_ai import *
import evo
import hyperopt
from hyperopt import hp
from hyperopt import fmin, tpe

rez_list = []
def objective(config):
    global rez_list
    evo = NetworkScene(search_type = "hyper_search")
    evo.set_config(config)
    score,search_index,conf,top_twenty_genomes,fitness_history = evo.runnn(30)
    top_twenty_genomes=sorted(top_twenty_genomes, reverse = True)
    rez_list.append([-score,search_index,config,top_twenty_genomes,fitness_history])
    
    rez_list=sorted(rez_list, key = lambda x:x[0])
    with open("hyper_search\\random_search\\hyper_final_rez","w") as w:
        for el in rez_list:
            for z in el:
                w.write(str(z)+"\n")
            w.write("\n")
    return score

if __name__ == '__main__':
    random.seed(a=None, version=2)
    space = {"bias_mutate_power":hp.uniform('a1',0,1),
            "bias_mutate_rate":hp.uniform('a2',0,1),
            "node_add_prob":hp.uniform('a3',0,1),
            "node_delete_prob":hp.uniform('a4',0,1),
            "weight_mutate_power":hp.uniform('a5',0,1),
            "weight_mutate_rate":hp.uniform('a6',0,1)}
    #evo = NetworkScene()

    #evo.runnn(100) 
    
    # with open("hyper_opt_rez","w") as w:
    #     pass
    #bayesian search
    best = fmin(objective, space, algo=hyperopt.rand.suggest, max_evals=300)
    print(best)
    print (hyperopt.space_eval(space, best))


    #hyper = {'bias_mutate_power': 1.5373687014265212, 'bias_mutate_rate': 0.080133756163907, 'node_add_prob': 0.3317219576299695, 'node_delete_prob': 0.32782958712312543, 'weight_mutate_power': 0.9679523155996961, 'weight_mutate_rate': 0.08272259947119626}
    # hyper = {'bias_mutate_power': 0.8163441767783309, 'bias_mutate_rate': 0.44307252775462147, 'node_add_prob': 0.5524862666457631, 'node_delete_prob': 0.4418819578994998, 'weight_mutate_power': 0.6021961631408529, 'weight_mutate_rate': 0.180829145166373}
    # e = evo.NetworkScene()
    # e.set_config(hyper)
    # e.runnn()
