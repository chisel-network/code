# Chisel MILP Solver

This repo contains the CHISEL solver in the encoding directory which uses Gurobi to solve a mixed-integer linear programming (MILP) problem. The problem involves finding the optimal allocation of spectrum to slices in an optical network.

## Requirements

- Python3
- Gurobi 
- NetworkX

## Usage

The main script is `chisel.py`, which takes the following arguments:

- `-g`, `--graph`: Path to the pickle file containing the network graph. Required argument.
- `-s`, `--slices`: Number of slices to allocate in the network. Required argument.
- `-d`, `--demands`: List of demands to sample slice demands from. Each demand is an integer in Gbps.
- `-r`, `--rand`: Seed for the random number generator. Optional argument. Use this for reproducable results.
- `-t`, `--time`: Time limit for the MIP solver in seconds. Optional argument. Default is 0 (no limit).
- `-e`, `--epsilon`: Weight allocated to the fragmentation objective. Optional argument. Default is 0 (no fragmentation objective).

To run the script, use the following command:

```bash
python3 chisel.py -s 25 -d 50 100 150 200 -r 1 -g ./IBM.gpickle -e 0.1
```

This command will solve the MILP problem for the network graph in ./IBM.gpickle with 25 slices and slice demands sampled from [50, 100, 150, 200]. It will use 1 as the random seed and 0.1 as the weight for the fragmentation objective.

Experiment with different networks provided (ATT, Abeline, IBM), number of slices, demand distribution and epsilon! 
Notice how the allocated spectrum moves towards the left in the logs as epsilon is increased!

Have fun experimenting :D

# Chisel Channel creator

We also have a script to create channels on ROADMs by one of the Vendors. This script can be found in the ```hardware``` directory.