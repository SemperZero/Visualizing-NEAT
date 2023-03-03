// SnakeLibrary.h
#pragma once

#ifdef SNAKELIBRARY_EXPORTS
#define SNAKELIBRARY_API __declspec(dllexport)
#else
#define SNAKELIBRARY_API __declspec(dllimport)
#endif

#include "CGeneration.h"

extern "C" SNAKELIBRARY_API NeatNN* create_net(int* input_layer_, int size_input_layer_, int* output_layer_, int size_output_layer_, bool render_game);

extern "C" SNAKELIBRARY_API NeatNode* create_node(int node_id_, double bias_, double response_, char* activation_function_, char* aggregation_function_);

extern "C" SNAKELIBRARY_API void add_connection(NeatNode * node, Connection con);

extern "C" SNAKELIBRARY_API void add_node(NeatNN* nn, NeatNode* node);

extern "C" SNAKELIBRARY_API int activate_net(NeatNN * nn, double* inputs_, int inputs_len_);

extern "C" SNAKELIBRARY_API CGeneration* create_c_generation(int population_size, int nr_gen);

extern "C" SNAKELIBRARY_API void add_c_net(CGeneration* cgen, NeatNN * nn);

extern "C" SNAKELIBRARY_API void play_c_generation(CGeneration* cgen, double* results, int population_size, int min_board_size, int max_board_size, int nr_tries, int nr_threads);

extern "C" SNAKELIBRARY_API double* create_array(int n);

extern "C" SNAKELIBRARY_API void clean_gen_memory(CGeneration * cgen); // calling this clears everything, as everything gets to be a part of this

extern "C" SNAKELIBRARY_API void clean_array(double* arr); // clean result array