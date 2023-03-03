#include "NeatNN.h"
#include <fstream>
#include <string>
#include<thread>
using namespace std;

class Location {
public:
    int x;
    int y;
    Location(){}
    Location(int x_, int y_)
    {
        x = x_;
        y = y_;
    }
};

static bool operator==(Location const& l1, Location const& l2)
{
    return l1.x == l2.x && l1.y == l2.y;
}

class Snake
{
public:
    Location head;
    vector<Location> tail;;
    int size;
    int start_size;
    enum directions { UP = 0, DOWN = 1, LEFT = 2, RIGHT = 3};
    Location map_dirs_poz[4] = { Location(0,1), Location(0,-1), Location(-1,0), Location(1,0) };
    directions direction;
    Location next_loc;
    Snake(){}
    Snake(Location spawn_point, int size_, directions spawn_dir)
    {
        head = spawn_point;
        direction = spawn_dir;
        start_size = size_;
        size = size_;
        directions tail_dir;
        directions inverse_direction[4] = { DOWN, UP, RIGHT, LEFT };
        tail_dir = inverse_direction[direction]; // old direction is encoded in the index ^^

        for (int i = 1; i <= size; i++)
        {
            tail.push_back(Location(head.x + map_dirs_poz[tail_dir].x * i, head.y + map_dirs_poz[tail_dir].y * i));
        }

    }
    void UpdateNextLoc()
    {
        next_loc = Location(head.x + map_dirs_poz[direction].x, head.y + map_dirs_poz[direction].y);

    }
    void Move()
    {
        for (int i = tail.size() - 1; i > 0; i--)
        {
            tail[i] = tail[i - 1];
        }
        tail[0] = head;
        head = next_loc;
    }
    void Grow()
    {
        Location last_tail_seg = tail[tail.size() - 1];
        tail.push_back(Location(last_tail_seg.x, last_tail_seg.y));
        size++;
    }
    ~Snake() {}
};

class Fruit {
public:
    Location loc;
    uniform_int_distribution<int> rand_x;
    uniform_int_distribution<int> rand_y;
    Fruit(){}
    Fruit(int& board_width, int& board_height)
    {
        rand_x = uniform_int_distribution<int>(1, board_width - 2);
        rand_y = uniform_int_distribution<int>(1, board_height - 2);
    }

    void Respawn(Snake& snake)
    {
        // maybe it's faster to add all free locs to dist and then choose one.
        // can make set/map with full places instead of going through all seg
        bool ok = 0;
        int x_;
        int y_;
        while (ok == 0) {
          
            ok = 1;
            x_ = rand_x(rng);
            y_ = rand_y(rng);

            if (x_ == loc.x && y_ == loc.y)
                ok = 0;
            if (x_ == snake.head.x && y_ == snake.head.y)
                ok = 0;
            for (Location seg : snake.tail)
                if (seg.x == x_ && seg.y == y_)
                    ok = 0;
        }
        loc.x = x_;
        loc.y = y_;
    }
};

class SimpleHash 
{public:
    unsigned long long d, h, p;
    SimpleHash()
    {
        d = 16777619;
        h = 0;
        p = 1;
    }

    void digest(int x)
    {
        h = h * d + x;
    }

    unsigned long long GetHash()
    {
        return h;
    }
};

class Game
{
public:
    NeatNN* nn;
    Snake snake;
    Fruit fruit;
    Location spawn_point;
    Snake::directions spawn_dir;
    int board_width;
    int board_height;
    int score;
    int nr_moves;
    int nr_moves_since_last_fruit;
    bool game_over;
    map<unsigned long long, int> hashes_states_count;
    uniform_int_distribution<int> rand_x;
    uniform_int_distribution<int> rand_y;
    uniform_int_distribution<int> rand_dir;
    bool render_game;

    Game(NeatNN* nn_, int board_width_, int board_height_) {
        render_game = nn_->render_game;
        if (render_game)
        {
            board_width_ = 20;
            board_height_ = 20;
        }
        nn = nn_;
        board_width = board_width_;
        board_height = board_height_;
        game_over = false;
        score = 0;
        nr_moves = 0;
        nr_moves_since_last_fruit = 0;
        rand_x = uniform_int_distribution<int>(2, board_width - 3);
        rand_y = uniform_int_distribution<int>(2, board_height - 3);
        rand_dir = uniform_int_distribution<int>(0,3);
        spawn_point = Location(rand_x(rng), rand_y(rng));
        spawn_dir = (Snake::directions)rand_dir(rng);
        snake = Snake(spawn_point, 1, spawn_dir);
        fruit = Fruit(board_width_, board_height_);//is this on stack while in game constructor?
        fruit.Respawn(snake);    
    }

    void Render()
    {
        system("cls");
        for (int i = 0; i < board_height; i++)
        {
            for (int j = 0; j < board_width; j++)
            {
                bool empty = true;
                if (i == 0 || i == board_height - 1 || j == 0 || j == board_width - 1)
                {
                    printf("#");
                    empty = false;
                }
                
                if (snake.head.y == i && snake.head.x == j)
                {
                    printf("O");
                    empty = false;
                }
                if (fruit.loc.y == i && fruit.loc.x == j)
                {
                    printf("X");
                    empty = false;
                }
                for (Location seg : snake.tail)
                {
                    if (seg.y == i && seg.x == j)
                    {
                        printf("o");
                        empty = false;
                    }
                }
                if (empty)
                {
                    printf(" ");
                }

            }
            printf("\n");
        }

       // this_thread::sleep_for(std::chrono::milliseconds(20));

    }

    bool CheckLoop()
    {
        //would be most correct to check this after moving, on new_loc, but it does not matter
        //function is not perfect. will have some false positives. this is why we check it only on small snake sizes
        //add vector of vectors, vector of states where info below is stored. check == on those vectors when hash is >=3 before returning true... or check it when ++
        //may make the entire code run slower than it would without checkloop and only with the comparison with 3*board_size
        //
        //what's the full impact of the false positives generated here, how often do they happen. does running the game 100 times cover it up in the average? what if it would cover a big breakthrough?
        SimpleHash hasher;
        hasher.digest(snake.head.x);
        hasher.digest(snake.head.y);

        for (Location seg : snake.tail)
        {
            hasher.digest(seg.x);
            hasher.digest(seg.y);

        }
        //no need to add fruit. cache is reset when it eats
        unsigned long long h = hasher.GetHash();
        if (hashes_states_count.count(h) == 0)
            hashes_states_count[h] = 1;
        else
            hashes_states_count[h]++;

        if (hashes_states_count[h] >= 4)
        {
           // printf("LOOPY LOOPY FOUND\n");
            return true;
            
        }

        return false;
    }

    bool CheckGameOver(Location new_loc)
    {
        if (new_loc.x == 0 || new_loc.y == 0 || new_loc.x == board_width - 1 || new_loc.y == board_height - 1)
            return true;
        
        for (Location seg : snake.tail)
            if (new_loc == seg)
                return true;

        //maybe add this in if size<20
        if (nr_moves_since_last_fruit > board_width * board_height * 3)
            return true;
     
        if(snake.size < 20)//2-3x speed
            
            if(CheckLoop())
               return true;

        return false;
    }

    double ai_input_sign(int a, int b)
    {
        if (a >= b)
            return 1;
        else
            return -1;
    }

    double peak_curve_point(double peak)
    {
        return -pow((peak - 1), 2) / (2 * peak - 1);
    }

    double normalize_space(double x, double peak)
    {
        double stretch, real_peak, t;
        stretch = board_width;
        real_peak = peak / stretch;
        t = peak_curve_point(real_peak);
        return 2 * (t - 1 / ((x-1) / stretch * 1 / (t * (t - 1)) + 1 / t)) - 1;//what are the domains?
    }

    double normalize_space_sig(double x, double peak)
    {
        return 2  / (1+exp(-(x- peak))) - 1;
      //  return 1 / (1 + exp(-(x - peak)));
    }

    double normalize_space_sig_1(double x, double peak)
    {
        //return 2 / (1 + exp(-(x - peak))) - 1;
          return 1 / (1 + exp(-(x - peak)));
    }

    void GetInputAI()
    {
        enum dirs { N, S, W ,E, N_E, S_E, S_W, N_W };
        int nr_dirs = 8;
        int nr_inputs = 26;
        double sin_45 = 0.7071;
        vector<double> vision_wall(nr_dirs, 0);
        vector<double> vision_tail(nr_dirs, max(board_width, board_height));
        vector<double> vision_fruit(4, 0);
        vector<double> nn_inputs;//could write directly here but the code would be nonsense
        nn_inputs.reserve(26);//can write directly here with an enum like this as index. wall_n, wall_e, wall_s_e, fruit_w, fruit_e,...
        int dist_N = board_height - snake.head.y;
        int dist_E = board_width - snake.head.x;

        vision_wall[N] = dist_N;
        vision_wall[S] = snake.head.y;
        vision_wall[W] = snake.head.x;
        vision_wall[E] = dist_E;
        vision_wall[N_E] = min(dist_N, dist_E) / sin_45;
        vision_wall[S_E] = min(dist_E, snake.head.y) / sin_45;
        vision_wall[S_W] = min(snake.head.x, snake.head.y) / sin_45;
        vision_wall[N_W] = min(snake.head.x, dist_N) / sin_45;

        for (Location seg : snake.tail)
        {
            int diff_x = seg.x - snake.head.x;
            int diff_y = seg.y - snake.head.y;
            if (seg.x == snake.head.x)
            {
                if (diff_y > 0)
                    vision_tail[N] = min(vision_tail[N], diff_y);
                else
                    vision_tail[S] = min(vision_tail[S], -diff_y);
                
            }
            if(seg.y == snake.head.y)
            {
                if (diff_x > 0)
                    vision_tail[E] = min(vision_tail[E], diff_x);
                else
                    vision_tail[W] = min(vision_tail[W], -diff_x);
            } 
            if (abs(seg.y - snake.head.y) == abs(seg.x - snake.head.x))
            {   //diag
                double dist = sqrt(pow((seg.y - snake.head.y),2) + pow((seg.x - snake.head.x),2) );
                if (diff_y > 0)//N
                {
                    if (diff_x)//E
                        vision_tail[N_E] = min(vision_tail[N_E], dist);
                    else//W
                        vision_tail[N_W] = min(vision_tail[N_W], dist);
                }
                else//S
                {
                    if (diff_x > 0)//E
                        vision_tail[S_E] = min(vision_tail[S_E], dist);
                    else//W
                        vision_tail[S_W] = min(vision_tail[S_W], dist);
                }
            }
        }

        vision_fruit[N] = ai_input_sign(fruit.loc.y, snake.head.y);
        vision_fruit[S] = -ai_input_sign(fruit.loc.y, snake.head.y);
        vision_fruit[W] = ai_input_sign(fruit.loc.y, snake.head.y);
        vision_fruit[E] = -ai_input_sign(fruit.loc.y, snake.head.y);

        double fruit_dist = sqrt(pow((fruit.loc.y - snake.head.y), 2) + pow((fruit.loc.x - snake.head.x), 2));
        double v;
        for (double val : vision_wall)
        {
            v = normalize_space_sig(val, 4);
            //v = 2*val / board_height;
            nn_inputs.push_back(v);// try 2*
        }
        for (double val : vision_tail)
        {
            v = normalize_space_sig(val, 4);
            //v = 2* val / board_height;
            nn_inputs.push_back(v);// try 2*
        }

        for (double val : vision_fruit)
            nn_inputs.push_back(val);//why adding sigmoid here does not work??

        int hot[4] = { 0,0,0,0 };
        hot[snake.direction] = 1;
        for (int i = 0; i < 4; i++)
            nn_inputs.push_back((double)hot[i]);

        /*vector<int> hot(4, 0);
        hot[snake.direction] = 1;
        for (int h : hot)
            nn_inputs.push_back(h);*/

        nn_inputs.push_back(snake.size);
        nn_inputs.push_back(fruit_dist);

        //magic line
        Snake::directions neuron_index_output = (Snake::directions)nn->ActivateNet(nn_inputs);

        Snake::directions prev_dir = snake.direction;
        Snake::directions new_dir = neuron_index_output;

        if ((prev_dir == Snake::directions::DOWN && new_dir == Snake::directions::UP) ||
            (prev_dir == Snake::directions::UP && new_dir == Snake::directions::DOWN) ||
            (prev_dir == Snake::directions::LEFT && new_dir == Snake::directions::RIGHT) ||
            (prev_dir == Snake::directions::RIGHT && new_dir == Snake::directions::LEFT))
        {
            new_dir = prev_dir;
        }
        snake.direction = new_dir;
    //    printf("head is %d, %d\n", snake.head.x, snake.head.y);
    }

    void Play()
    {

        while (!game_over)
        {
            GetInputAI();
            snake.UpdateNextLoc();
            game_over = CheckGameOver(snake.next_loc);
            if (snake.next_loc == fruit.loc)
            {
                snake.Grow();
                fruit.Respawn(snake);
                nr_moves_since_last_fruit = 0;
                hashes_states_count.clear();
                score++;
            }
            snake.Move();
            if (render_game)
            {
                Render();
                if (game_over)
                    this_thread::sleep_for(std::chrono::milliseconds(1000));
            }
            nr_moves++;
            nr_moves_since_last_fruit++;
        }
    }

    int GetScore()
    {
      //  return (snake.size - snake.start_size)*10000/(board_width*board_height);
        return snake.size - snake.start_size;
    }
    

};