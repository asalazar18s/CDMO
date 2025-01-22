import os
import re
import sys
import json

TIMEOUT = 300
# OPT[i] = Optimal value for instance i. 
OPT = [None, 14, 226, 12, 220, 206]

def read_json_file(file_path):
    try:
        with open(file_path, 'r') as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
        return None
    except json.JSONDecodeError:
        print(f"Error: Unable to parse JSON from file '{file_path}'.")
        return None

def check_single_instance(input_folder, results_folder, instance_number):
    errors = []
    warnings = []

    results_file = f'inst{instance_number}.json'
    inst_file_path = os.path.join(input_folder, f'inst{instance_number}.dat')
    results_file_path = os.path.join(results_folder, results_file)

    print(f'\nChecking results for instance {instance_number}')
    
    # Read instance input file
    with open(inst_file_path) as inst_file:
        i = 0        
        for line in inst_file:
            if i == 0:
                n_couriers = int(line)
            elif i == 1:
                n_items = int(line)
                dist_matrix = [None] * (n_items + 1)
            elif i == 2:
                capacity = [int(x) for x in line.split()]
                assert len(capacity) == n_couriers
            elif i == 3:
                sizes = [int(x) for x in line.split()]
                assert len(sizes) == n_items
            else:
                row = [int(x) for x in line.split()]
                assert len(row) == n_items + 1
                dist_matrix[i-4] = [int(x) for x in row]
            i += 1
    
    for i in range(len(dist_matrix)):
        assert dist_matrix[i][i] == 0
    
    # Read results file
    results = read_json_file(results_file_path)
    
    if results is None:
        print(f"Results file {results_file_path} could not be read.")
        return

    for solver, result in results.items():
        print(f'\t\tChecking solver {solver}')
        header = f'Solver {solver}, instance {instance_number}'
        if result['time'] < 0 or result['time'] > TIMEOUT:
            errors.append(f"{header}: runtime unsound ({result['time']} sec.)")
        if 'sol' not in result or not result['sol'] or result['sol'] == 'N/A':
            continue
        max_dist = 0
        n_collected = sum(len(p) for p in result['sol'])
        if n_collected != n_items:
            errors.append(f"{header}: solution {result['sol']} collects {n_collected} instead of {n_items} items")
        courier_id = 0
        for path in result['sol']:
            dist = 0
            path_size = 0
            # Adjusting with origin point.
            path = [n_items+1] + path + [n_items+1]          
            for i in range(1, len(path)):
                curr_item = path[i] - 1
                prev_item = path[i-1] - 1            
                dist += dist_matrix[prev_item][curr_item]
                if i < len(path) - 1:
                    path_size += sizes[curr_item]
            if path_size > capacity[courier_id]:
                errors.append(f"{header}: path {path} of courier {courier_id} has total size {path_size}, exceeding its capacity {capacity[courier_id]}")
            if dist > max_dist:
                max_dist = dist
                max_path = path
                max_cour = courier_id
            courier_id += 1
        if max_dist != result['obj']:
            errors.append(f"{header}: objective value {result['obj']} inconsistent with max. distance {max_dist} of path {max_path}, courier {max_cour})")
        i = int(instance_number)
        if i < 6:
            if result['optimal']:
                if result['obj'] != OPT[i]:
                    errors.append(f"{header}: claimed optimal value {result['obj']} inconsistent with actual optimal value {OPT[i]})")
            else:
                warnings.append(f"{header}: instance {instance_number} not solved to optimality")

    print('\nCheck terminated.')
    if warnings:
        print('Warnings:')
        for w in warnings:
            print(f'\t{w}')
    if errors:
        print('Errors detected:')
        for e in errors:
            print(f'\t{e}')
    else:
        print('No errors detected!')

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python solution_checker.py <input folder> <results folder> <instance number>")
        sys.exit(1)

    input_folder = sys.argv[1]
    results_folder = sys.argv[2]
    instance_number = sys.argv[3]
    
    check_single_instance(input_folder, results_folder, instance_number)
