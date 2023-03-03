#pragma once
#include "SnakeGame.h"
#include<thread>
#include<iostream>
using namespace std;

static auto threaded_play = [](vector<NeatNN*>& net_batch, int nr_tries, int min_board_size, int max_board_size, vector<double>& results_batch, int nr_gen)
{
	uniform_int_distribution<int> rand_dist = uniform_int_distribution<int>(min_board_size, max_board_size);
	//uniform_int_distribution<int> rand_y = uniform_int_distribution<int>(min_board_size, max_board_size);


	auto last_time = chrono::steady_clock::now();

	auto current_time = chrono::steady_clock::now();
		

	for (int t = 0; t < nr_tries; t++)
	{
	//	if(t%100 ==0)
	//		printf("running thread id: %d | %d\n", std::this_thread::get_id(), t);
		int z = rand_dist(rng);//trb invers for-urile pentru ca toate net-urile sa joace pe acelasi size

		for (int i = 0; i < net_batch.size(); i++)
		{
				Game* g = new Game(net_batch[i], z, z);
				g->Play();
				double x = (double)g->GetScore();
				results_batch[i] += x;
				delete g;//calls game destructor
				current_time = chrono::steady_clock::now();
				auto elapsed = chrono::duration_cast<chrono::milliseconds>(current_time - last_time).count();
				int cooling_cycle;
				if (nr_gen < 50)
					cooling_cycle = 4;
				else
					cooling_cycle = 4;

				if (elapsed > cooling_cycle)
				{

					this_thread::sleep_for(std::chrono::milliseconds(2));
					last_time = chrono::steady_clock::now();

				}
		}
	}

	for (int i = 0; i < results_batch.size(); i++)
	{
		results_batch[i] = results_batch[i] / nr_tries;
	}

};

class CGeneration
{
public:
	int population_size;
	vector<NeatNN*> neural_networks;
	int nr_gen;
	CGeneration(){}
	CGeneration(int population_size_, int nr_gen_)
	{
		population_size = population_size_;
		neural_networks.reserve(population_size_);
		nr_gen = nr_gen_;
	}

	~CGeneration()
	{
		for (int i = 0; i < neural_networks.size(); i++)
			delete neural_networks[i];
	}

	void AddNet(NeatNN* nn)
	{
		neural_networks.push_back(nn);
	}

	void PlayAllGames(double* results, int population_size_, int min_board_size, int max_board_size, int nr_tries, int nr_threads)
	{
		if (population_size_ != population_size)
		{
			printf("WRONG POPULATION SIZE %d, %d", population_size_, population_size);
			exit(-1);
		}

		int chunk_size = (int)ceil((float)population_size_ / (float)nr_threads);//do this better. 6 6 6 6 5 5 5 5, no 7 7 7 7 7 7 1 or something like this
		vector<vector<NeatNN*>> net_batches(nr_threads);
		vector<vector<double>> results_batches(nr_threads);
		int k = -1;
		for (int i = 0; i < neural_networks.size(); i++)
		{
			if (i % chunk_size == 0)
				k++;
			net_batches[k].push_back(neural_networks[i]);

		}

		if (net_batches.size() != nr_threads)
		{
		 	printf("WRONG BATCH SIZE %d, %d\n", net_batches[k].size(), nr_threads);
			exit(-1);
		}

		vector<thread> thread_functions;

		for (int i = 0; i < nr_threads; i++)
		{
			results_batches[i] = vector<double>(chunk_size, 0);
			thread_functions.push_back(thread(threaded_play, std::ref(net_batches[i]), nr_tries, min_board_size, max_board_size, std::ref(results_batches[i]), nr_gen ));
		}


		for (int i = 0; i < nr_threads; i++)
		{
			
			thread_functions[i].join();
			
		}


		for (int i = 0; i < neural_networks.size(); i++)
		{
			results[i] = results_batches[i / chunk_size][i % chunk_size];//does this work?
		}
	}

};

