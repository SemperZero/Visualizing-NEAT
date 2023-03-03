// SnakeLibrary.cpp : Defines the exported functions for the DLL.
#include "pch.h" // use stdafx.h in Visual Studio 2017 and earlier
#include "SnakeLibrary.h"

NeatNN* create_net(int* input_layer_, int size_input_layer_, int* output_layer_, int size_output_layer_, bool render_game_)
{
    NeatNN* nn = new NeatNN(input_layer_, size_input_layer_, output_layer_, size_output_layer_, render_game_);
    return nn;
}

NeatNode* create_node(int node_id_, double bias_, double response_, char* activation_function_, char* aggregation_function_)
{
    NeatNode* node = new NeatNode(node_id_, bias_, response_, activation_function_, aggregation_function_);
    return node;
}

void add_connection(NeatNode* node, Connection con)
{
    node->AddConnection(con);
}

void add_node(NeatNN* nn, NeatNode* node)
{
    nn->AddNode(node);
}

int activate_net(NeatNN* nn, double* inputs_, int inputs_len_)
{
    vector<double> inputs;

    inputs.assign(inputs_, inputs_ + inputs_len_);
    int rez = nn->ActivateNet(inputs);

    return rez;
}

CGeneration* create_c_generation(int population_size, int nr_gen)
{
    CGeneration* g =new CGeneration(population_size, nr_gen);
    return g;
}

void add_c_net(CGeneration* cgen, NeatNN* nn)
{
    cgen->AddNet(nn);
}

void play_c_generation(CGeneration* cgen, double* results, int population_size, int min_board_size, int max_board_size, int nr_tries, int nr_threads)
{
    cgen->PlayAllGames(results, population_size, min_board_size, max_board_size, nr_tries, nr_threads);
}

double* create_array(int n)
{
    double* a = new double[n];
    for (int i = 0; i < n; i++)
    {
        a[i] = 0.0;
    }
    return a;
}

void clean_gen_memory(CGeneration* cgen)
{
    delete cgen;
}

void clean_array(double* arr)
{
    delete[] arr;
}

