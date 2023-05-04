import random
import pdb
from itertools import islice
from helper import *
import networkx as nx
from Topology import *
from consts import *
import pickle
import threading
import concurrent.futures
import os
import sys


def parse_network_topology(name, file_path):
    G = nx.read_gpickle(file_path)
    G_cc = sorted(nx.connected_components(G), key=len, reverse=True)
    G = G.subgraph(G_cc[0])
    network = OpticalNetwork(name)
    initspectrums = []

    topology_file = open('cloudwan.txt', 'w')

    for edge in G.edges:
        initspectrum = G.get_edge_data(*edge)["pixel_count"]
        
        free_spectrum_bits = 0
        for pixel in initspectrum:
            if initspectrum[pixel] == 0:
                free_spectrum_bits += 1
        
        assert(len(initspectrum) == GLOBAL_SWITCH_PIXELS)
        initspectrums.append(initspectrum)
        assert (edge[0], edge[1]) not in network.fiberspans
        assert (edge[1], edge[0]) not in network.fiberspans
        network.add_fiberspan(edge[0], edge[1], initspectrum, GLOBAL_SWITCH_PIXELS)
        # from, to, empty_bits
        topology_file.write('{},{},{}\n'.format(edge[0], edge[1], free_spectrum_bits))
        network.add_fiberspan(edge[1], edge[0], initspectrum, GLOBAL_SWITCH_PIXELS)
        topology_file.write('{},{},{}\n'.format(edge[1], edge[0], free_spectrum_bits))
    
    topology_file.close()
    # with open('spectrums.pkl', 'wb') as pickle_file:
    #     pickle.dump(initspectrums, pickle_file)
    return G, network

def get_distance_file_path():
    return os.path.join('./', 'distances.pickle')

def get_ksp_file_path():
    return os.path.join('./', 'ksps.pickle')

def get_ksps_dict():
    ksps_path = get_ksp_file_path()
    # Commenting to keep sites anonymous
    # if os.path.isfile(ksps_path):
    #     with open(ksps_path, 'rb') as pickle_file:
    #         return pickle.load(pickle_file)
    return {}

def put_ksps_dict(ksps):
    ksps_path = get_ksp_file_path()
    # if os.path.isfile(ksps_path):
    #     print('NOT SAVING KSPS ALREADY EXISTS')
    #     return
    # with open(ksps_path, 'wb') as pickle_file:
    #     pickle.dump(ksps, pickle_file)

def get_distance_dict():
    distance_file_path = get_distance_file_path()
    # Commenting to keep sites anonymous
    # if os.path.isfile(distance_file_path):
    #     with open(distance_file_path, 'rb') as pickle_file:
    #         return pickle.load(pickle_file)
    return {}

def put_distance_dict(distances):
    distance_file_path = get_distance_file_path()
    # if os.path.isfile(distance_file_path):
    #     print('NOT SAVING DISTANCE ALREADY EXISTS')
    #     return
    # with open(distance_file_path, 'wb') as pickle_file:
    #     pickle.dump(distances, pickle_file)

def k_shortest_paths(G, source, target, k):
    return list(islice(nx.shortest_simple_paths(G, source, target), k))

def parse_paths(network, nxnetwork, should_cache):
    num_switches = len(network.opswitches)
    print('Number of nodes in G: {}, number of edges in G: {}'.format(nxnetwork.number_of_nodes(), nxnetwork.number_of_edges()))
    print('Number of paths to parse: {}'.format(num_switches * num_switches - num_switches))
    num_parsed = 0
    if should_cache:
        print('[CACHE]: YES')
        FiberPath.coords_to_distances = get_distance_dict()
        ksps = get_ksps_dict()
    else:
        print('[CACHE]: NO')
        FiberPath.coords_to_distances = {}
        ksps = {}

    for node1 in network.opswitches:
        for node2 in network.opswitches:
            if node1 == node2: continue
            if (node1, node2) in ksps:
                ksp = ksps[(node1, node2)]
            else:
                ksp = k_shortest_paths(nxnetwork, node1, node2, 5)
                ksps[(node1, node2)] = ksp
            for path in ksp:
                path_obj = network.add_fiberpath(path)
            num_parsed += 1
            if num_parsed % 100 == 0:
                print('Number of paths parsed: {}'.format(num_parsed))

    if should_cache:
        print('[CACHE]: Yes, so storing pickles')
        put_distance_dict(FiberPath.coords_to_distances)
        put_ksps_dict(ksps)

def generate_slice_demands(network, num_demands, demand_bw_list):
    sites = set()
    for slice_tuple in network.fiberspans:
        sites.add(slice_tuple[0])
        sites.add(slice_tuple[1])
    sites = list(sites)

    slices_tuples = []
    sites.sort()

    while len(slices_tuples) < num_demands:
        src = random.choice(sites)
        dst = random.choice(sites)
        slice_tuple = (src, dst)
        if src == dst or slice_tuple in network.fiberspans or slice_tuple in slices_tuples:
            continue
        slices_tuples.append(slice_tuple)

    # demand_bw_list = [50, 100, 150, 200]
    print('Generating {} slices from the demands {}'.format(len(slices_tuples), demand_bw_list))
    demands_file = 'demands_{}.txt'.format(num_demands)
    demands_file = open(demands_file, 'w')
    for src, dst in slices_tuples:
        demand = random.choice(demand_bw_list)
        network.add_slice(src, dst, demand)
        demands_file.write('{},{},{}\n'.format(src, dst, demand))
    demands_file.close()
    
    
