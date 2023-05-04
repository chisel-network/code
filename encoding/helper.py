import pdb
from Topology import *
from consts import GLOBAL_SWITCH_PIXELS
import math
import statistics

def initialize_optimization_vars(model, network):
    print("Initialize variables for all slices")
    for slice in network.slices.values():
        slice.init_width_var(model)
        slice.init_path_selection_var(model)
        slice.init_spectrum_var(model, GLOBAL_SWITCH_PIXELS)
        slice.init_toggle_var(model, GLOBAL_SWITCH_PIXELS)
        
def add_unique_path_per_slice_constraints(model, network):
    for slice in network.slices.values():
        model.Assert(sum(slice.path_vars) == 1)

def add_non_overlapping_spectrumm_constraints(model, network):
    for fiberspan in network.fiberspans.values():
        for pixel in range(GLOBAL_SWITCH_PIXELS):
            init_pixel = fiberspan.init_spectrum[pixel]
            sum_pixel_utilization = init_pixel
            for slice_tuple, slice in network.slices.items():
                for path_idx, path_var in enumerate(slice.path_vars):
                    path_obj = slice.paths[path_idx]
                    if fiberspan in path_obj.path:
                        sum_pixel_utilization += \
                            path_var * slice.spectrum_var[0, pixel]
            model.Assert(sum_pixel_utilization <= 1)
                    
def add_spectral_width_constraints(model, network):
    for slice_tuple, slice in network.slices.items():
        model.Assert(slice.w_var == sum(slice.spectrum_var.values()))

def add_slice_bw_constraints(model, network):
    for slice_tuple, slice in network.slices.items():
        for path_idx, path_var in enumerate(slice.path_vars):
            path_obj = slice.paths[path_idx]
            modulation = path_obj.modulation
            bandwidth_rounded = math.ceil(slice.bandwidth / modulation) * modulation
            model.Assert((path_var == 1) >> (slice.w_var * path_obj.modulation <= bandwidth_rounded))

def add_wavelength_contiguity_constraints(model, network):
    # Add a constraint between every fiberSpan’s every slice’s x (Spectrum_var) with that slice’s toggle vector t.
    for slice_tuple, slice in network.slices.items():
        x = slice.spectrum_var
        t = slice.t_var
        # add constraint 7, 8, 9 between slice_obj's toggle variable and fiberspan's spectrum_var

        model.problem.addConstrs(x[0, j - 1] <= x[0, j] + t[0, j] for j in range(1, GLOBAL_SWITCH_PIXELS))
        model.problem.addConstrs(t[0, j - 1] <= t[0, j] for j in range(1, GLOBAL_SWITCH_PIXELS))
        model.problem.addConstrs(t[0, j] + x[0, j] <= 1 for j in range(GLOBAL_SWITCH_PIXELS))

def print_vector(vector, name, size):
    vector_str = ",".join([str(round(vector[0, i].X)) for i in range(size)])
    print(f"[{name}]: {vector_str}")

def get_average_hole_size(vector):
    hole_sizes = []
    current_size = 0
    for pixel in vector:
        # pixel = vector[idx]
        if pixel == 0:
            current_size += 1
        elif pixel == 1:
            if current_size > 0:
                hole_sizes.append(current_size)
            current_size = 0
    
    if len(hole_sizes) == 0:
        return 0
    
    print(hole_sizes)
    return statistics.mean(hole_sizes)

def round_bool(value):
    if value > 0.8:
        return 1
    return 0

def print_slice_allocations(model, network):
    for slice_tuple, slice in network.slices.items():
        slice_name = f"TOGGLE {slice.source} to {slice.destination}, bw {slice.bandwidth}"
        # print(f'[Slice Info begin]: {slice_name}')
        # print_vector(slice.t_var, slice_name, GLOBAL_SWITCH_PIXELS)    
        for path_idx, path_var in enumerate(slice.path_vars):
            path_obj = slice.paths[path_idx]
            for fiberspan in network.fiberspans.values():
                if fiberspan in path_obj.path and round(path_var.X) > 0:
                    x = slice.spectrum_var
                    x_name = f"SPAN {fiberspan.srcsite} to {fiberspan.destsite}"
                    # vector_str = ",".join([str(round(x[0, i].X) + fiberspan.init_spectrum[i]) for i in range(GLOBAL_SWITCH_PIXELS)])
                    # print(f"[{x_name} MERGED INIT]: {vector_str}")     
                    # print_vector(x, x_name, GLOBAL_SWITCH_PIXELS)        

                    # checking correctness
                    for i in range(GLOBAL_SWITCH_PIXELS):
                        assert(round(x[0, i].X) + fiberspan.init_spectrum[i] <= 1)
    
    print('Checking correctness of common  bits on spans')   
    assert_count = 0 
    # Also check no two slices have a common bit set
    for _, slice_1 in network.slices.items():
        for _, slice_2 in network.slices.items():
            if slice_1 == slice_2:
                continue
            
            x_1 = slice_1.spectrum_var
            x_2 = slice_2.spectrum_var
            path_1 = []
            path_2 = []
            for path_idx, path_var in enumerate(slice_1.path_vars):
                if round(path_var.X) > 0:
                    path_1.append(slice_1.paths[path_idx])

            for path_idx, path_var in enumerate(slice_2.path_vars):
                if round(path_var.X) > 0:
                    path_2.append(slice_2.paths[path_idx])

            assert(len(path_1) <= 1)
            assert(len(path_2) <= 1)

            if len(path_1) > 0 and len(path_2) > 0:
                path_1 = path_1[0].path
                path_2 = path_2[0].path
                common_spans = [fiberspan for fiberspan in path_1 if fiberspan in path_2]
                if len(common_spans) > 0:
                    for i in range(GLOBAL_SWITCH_PIXELS):
                        assert(round(x_1[0, i].X) + round(x_2[0, i].X) <= 1)
                        assert_count += 1
    
    print('Asserted : {} times'.format(assert_count))

    # Assert pixel usage
    for fiberspan in network.fiberspans.values():
        spectrum = []
        for pixel in range(GLOBAL_SWITCH_PIXELS):
            init_pixel = fiberspan.init_spectrum[pixel]
            sum_pixel_utilization = init_pixel
            for slice_tuple, slice in network.slices.items():
                for path_idx, path_var in enumerate(slice.path_vars):
                    path_obj = slice.paths[path_idx]
                    if fiberspan in path_obj.path:
                        sum_pixel_utilization += round(path_var.X) * round(slice.spectrum_var[0, pixel].X)
            sum_pixel_utilization = math.floor(sum_pixel_utilization)
            if sum_pixel_utilization > 1:
                print('ERROR: {}'.format(sum_pixel_utilization))
            assert(sum_pixel_utilization <= 1)
            spectrum.append(sum_pixel_utilization)
        
        average_hole_len = get_average_hole_size(spectrum)
        

        print('[HOLES]: {} {}'.format(fiberspan.name, average_hole_len))
        print('[SPECTRUM]: {}'.format(",".join([str(s) for s in spectrum])))

def add_constraints(model, network):
    print("Unique path constraints")
    add_unique_path_per_slice_constraints(model, network)
    print("Non-overlapping spectrum constraints")
    add_non_overlapping_spectrumm_constraints(model, network)
    print("Spectral width constraints")
    add_spectral_width_constraints(model, network)
    print("Slice bandwidth cosntraints")
    add_slice_bw_constraints(model, network)
    print("Wavelength contiguity constraints")
    add_wavelength_contiguity_constraints(model, network)


def get_objective(model, network):
    objective = 0
    for slice_tuple, slice in network.slices.items():
        for path_idx, path_var in enumerate(slice.path_vars):
            path_obj = slice.paths[path_idx]
            objective += path_var * slice.w_var * path_obj.modulation

    return objective

def get_fragmentation_objective(model, network):
    objective = 0
    for slice_tuple, slice in network.slices.items():
        for path_idx, path_var in enumerate(slice.path_vars):
            path_obj = slice.paths[path_idx]
            t = slice.t_var
            # objective += path_var * path_obj.modulation * sum([t[0, j] for j in range(GLOBAL_SWITCH_PIXELS)])
            objective += path_var * path_obj.modulation * sum([t[0, j] for j in range(GLOBAL_SWITCH_PIXELS)])

    return objective

def print_slices(model, network):
    for slice_tuple, slice in network.slices.items():
        for path_idx, path_var in enumerate(slice.path_vars):
            path_obj = slice.paths[path_idx]
            if path_var.X > 0:
                allocation = round(path_var.X) * round(slice.w_var.X) * path_obj.modulation
                print('[ALLOCATION] {} {}: {}/{}'.format(path_obj.modulation, slice_tuple, allocation, slice.bandwidth))
