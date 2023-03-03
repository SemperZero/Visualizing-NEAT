#pragma once
#include <vector>
#include <string>
#include <map>
#include <math.h>
#include <iostream>
#include <random>
using namespace std;
static random_device rd;
static mt19937 rng(rd());

typedef struct{
	int node_id;
	double connection_weight;
} Connection;

class NeatNode {
public:
	int node_id;
	double bias;
	double response;
	string activation_function;
	string aggregation_function;
	vector<Connection> connections;//these are defined in python, it's fine. won't corrupt memory once function ends and stack gets overwritten so no need for *

	NeatNode(int node_id_, double bias_, double response_, char* activation_function_, char* aggregation_function_)
	{
		node_id = node_id_;
		bias = bias_;
		response = response_;
		activation_function = activation_function_;
		aggregation_function = aggregation_function_;
	}

	NeatNode(int node_id_, double bias_, double response_, char* activation_function_, char* aggregation_function_, Connection* connections_, int len_connections_)
	{
		node_id = node_id_;
		bias = bias_;
		response = response_;
		activation_function = activation_function_;
		aggregation_function = aggregation_function_;
		connections.assign(connections_, connections_ + len_connections_);
	}

	void PrintNeatNode(double val)
	{
		printf("	NeatNode id: %d\n", node_id);
		printf("	val: %f, bias: %f, response: %f\n", val, bias, response);
		printf("	activation: %s, aggregation: %s\n", activation_function, aggregation_function);
		printf("	connections:{\n");
		for (Connection c : connections)
		{
			printf("	  con id: %d, con weight: %f\n", c.node_id, c.connection_weight);
		}
		printf("	}\n");

	}
	
	void AddConnection(Connection con)
	{
		connections.push_back(con);//this does a copy on con. interesting. would be more efficient to allocate array of structs in c and assign it here
	}

};

class NeatNN{	
public:
	vector<NeatNode*> neat_nodes;
	vector<int> input_nodes_ids;
	vector<int> output_nodes_ids;
	map<int, double> nodes_id_val;
	uniform_real_distribution<double> real_uniform;
	bool render_game;

	NeatNN(int* input_layer_, int size_input_layer_, int* output_layer_, int size_output_layer_, bool render_game_)
	{
		input_nodes_ids.assign(input_layer_, input_layer_ + size_input_layer_);
		output_nodes_ids.assign(output_layer_, output_layer_ + size_output_layer_);
		for (int i : input_nodes_ids)
			nodes_id_val[i] = 0;

		for (int i : output_nodes_ids)
			nodes_id_val[i] = 0;

		render_game = render_game_;
		real_uniform = uniform_real_distribution<double>(0.0, 1.0);
	}

	~NeatNN()
	{
		for (int i = 0; i < neat_nodes.size(); i++)
			delete neat_nodes[i];
	}

	void AddNode(int node_id_, double bias_, double response_, char* activation_function_, char* aggregation_function_, Connection* connections, int len_connections_)
	{   //can use predefined size
		NeatNode* n = new NeatNode(node_id_, bias_, response_, activation_function_, aggregation_function_, connections, len_connections_);
		neat_nodes.push_back(n);
		nodes_id_val[node_id_] = 0;
	}

	void AddNode(NeatNode* node)
	{   
		neat_nodes.push_back(node);
		nodes_id_val[node->node_id] = 0;
	}

	void Softmax(vector<double> &input) {

		int i;
		double m, sum, constant;

		m = -INFINITY;
		for (i = 0; i < input.size(); ++i) {
			if (m < input[i]) {
				m = input[i];
			}
		}

		sum = 0.0;
		for (i = 0; i < input.size(); ++i) {
			sum += exp(input[i] - m);
		}

		constant = m + log(sum);
		for (i = 0; i < input.size(); ++i) {
			input[i] = exp(input[i] - constant);
		}

	}

	int WeightedChooseOutput(vector<double>& softmaxed_outputs) {
		double rand_nr = real_uniform(rng);
		double prev_nr = 0;
		double next_nr = 0;
		//printf("rand_nr is %f\n", rand_nr);
		for (int i = 0; i < softmaxed_outputs.size(); i++)
		{
			next_nr = prev_nr + softmaxed_outputs[i];
			if(prev_nr <= rand_nr && rand_nr <= next_nr)// < or <=?
			{
				return i;
			}
			prev_nr = next_nr;

		}
		
		printf("Weighted choice is wrong\n");

		printf("output sotfmaxed:\n");
		for (auto o : softmaxed_outputs)
			printf("%f, ", o);
		printf("\nrand_nr is %f\n", rand_nr);

		printf("\n");

		exit(-1);
		
		return -1;
	}

	// would be more clean if we return output vector and then do the choice in game class
	int ActivateNet(vector<double> inputs)
	{	//should we make sure everything is ok by using id+vals or just send vals
		/*printf("start activation\n");
		printf("C_input: ");
		for (double el : inputs)
		{
			printf("%f, ", el);
		}
		printf("\n");*/
		
		if (inputs.size() != input_nodes_ids.size())
		{
			cout << "NR inputs invalid. got: " << inputs.size() << " expected: " << input_nodes_ids.size() << endl;
			exit(-1);
			//add error here
		}
		for (int i = 0; i< inputs.size(); i++)
		{
			nodes_id_val[input_nodes_ids[i]] = inputs[i];
		}
		
		
		for (NeatNode* node : neat_nodes)
		{
			double s = 0;
			double result = 0;
			//printf("	in node %d\n", node->node_id);
			for (Connection con : node->connections)
			{
			//	printf("		con node: (id:%d, val: %f), con weight val: %f\n", con.node_id, nodes_id_val[con.node_id], con.connection_weight);
				s += nodes_id_val[con.node_id] * con.connection_weight;
			}

			if (node->activation_function == "relu")
			{
				s = node->bias + node->response * s;
				result = (s > 0) ? s : 0;
				
			}else if(node->activation_function == "sigmoid")
			{
				s = node->bias + node->response * s;
				s = max(-60.0, min(60.0, 5.0 * s));
				result = 1.0 / (1.0 + exp(-s));
			}
			else {
				printf("UNKNOWN ACTIVATION FUNCTION: %s.", node->activation_function);
				exit(-1);
			}

			nodes_id_val[node->node_id] = result;
		}

		
		//PrintNet();
		
		double max_val = 0;
		int max_id = 0;
		
		vector<double> output_values(output_nodes_ids.size());

		for (int i = 0; i< output_nodes_ids.size(); i++)
		{
			output_values[i] = nodes_id_val[output_nodes_ids[i]];

		}
		Softmax(output_values);
		/*	printf("output:\n");
		for (auto o : output_values)
			printf("%f, ", o);
		printf("\n");

		

		printf("output sotfmaxed:\n");
		for (auto o : output_values)
			printf("%f, ", o);
		printf("\n\n");*/


		int return_index = WeightedChooseOutput(output_values);

		return return_index;
		//check order is always the same in output nodes. or make reverse map from id to index to direction


		/*long double max_val = 0;
		int max_id = 0;


		for (int id : output_nodes_ids)
		{
			if (nodes_id_val[id] > max_val)
			{
				max_val = nodes_id_val[id];
			}
		}

		vector<int> max_output_indexes;
		for (int i = 0; i < output_nodes_ids.size(); i++)
		{
			if (nodes_id_val[output_nodes_ids[i]] == max_val)
			{
				max_output_indexes.push_back(i);
			}
		}

		std::uniform_int_distribution<int> rand_output(0, max_output_indexes.size() - 1);
		int rand_index = rand_output(rng);

		return max_output_indexes[rand_index];*/
	}
	
	void PrintNet()
	{
		printf("C NET:\n");
		printf("input_nodes: [");
		for (int n : input_nodes_ids)
		{
			printf("%d, ", n);
		}
		printf("]\n");

		printf("output_nodes: [");
		for (int n : output_nodes_ids)
		{
			printf("%d, ", n);
		}
		printf("]\n");

		printf("input vals: [");
		for (int n : input_nodes_ids)
		{
			printf("%f, ", nodes_id_val[n]);
		}
		printf("]\n");

		printf("output vals: [");
		for (int n : output_nodes_ids)
		{
			printf("%f, ", nodes_id_val[n]);
		}
		printf("]\n");

		for (NeatNode* n : neat_nodes)
		{
			n->PrintNeatNode(nodes_id_val[n->node_id]);
		}
	}
};

