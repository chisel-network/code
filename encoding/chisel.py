import pdb
from parser import *
from helper import *
from MIPSolver import *
import argparse
import os

parser = argparse.ArgumentParser()

parser.add_argument("-g", "--graph", help="Path to the pickle file containing the graph", type=str)
parser.add_argument("-s", "--slices", help="number of slices", type=int)
parser.add_argument("-d", "--demands", help="list of demands to sample slice demands from", type=int, nargs='+')
parser.add_argument("-r", "--rand", help='Seed for the random number generator', type=int)
parser.add_argument("-t", '--time', help='time limit for the MIP solver', default=0, type=int)
parser.add_argument("-nc", '--no_cache', help='Disable cached ksps and distance', default=False, action="store_true")
parser.add_argument("-e", "--epsilon", help="Weight allocated to the fragmentation objective", default=0, type=float)

args = parser.parse_args()
should_cache = not args.no_cache
print('Cache is: {}, time is: {}'.format(should_cache, args.time))

def make_network(name):
    print('Parsing network topology')
    # TODO: get graph file path from CLI and pass it to parse_network_topology
    file_path = args.graph
    nxnetwork, network = parse_network_topology(name, file_path)
    print('Generate slice demands')
    # TODO: make the number of slices a CLI parameter
    # TODO: make the range of slice demands chosen from a parameter
    generate_slice_demands(network, args.slices, args.demands)
    print('Parse paths')
    parse_paths(network, nxnetwork, should_cache)
    model = GurobiSolver()
    print('Initializing optimization variables')
    initialize_optimization_vars(model, network)
    print('Adding constraints')
    add_constraints(model, network)
    return model, network

print('Setting seed to {}'.format(args.rand))

random.seed(args.rand)
model, network = make_network("cloudwan")
objective = get_objective(model, network)
fragmentation_objective = get_fragmentation_objective(model, network)
print('Epsilon is : {}'.format(args.epsilon))

model.Maximize(objective + (args.epsilon * fragmentation_objective))

if args.time > 0:
    model.problem.Params.TimeLimit = args.time
else:
    print('SETTING MIP GAP')
    model.problem.Params.MIPGap = 0.02 # 2%

model.Solve()
print_slices(model, network)
print_slice_allocations(model, network)