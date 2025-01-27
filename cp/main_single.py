'''
This script integrates various stages: 
1. Converts a .dat file to a .dzn format suitable for MiniZinc processing.
2. Sets up and runs the MiniZinc model instance, specfying the solver to find solutions for the provided problem instance.
3. Produces the output in form of JSON format.
'''

import os
import numpy as np
from minizinc import Instance, Model, Solver
import datetime
import json

def convert_dat_to_dzn(dat_file, dzn_file):
    with open(dat_file, 'r') as f:
        lines = f.readlines()
    
    num_couriers = int(lines[0].strip())
    num_load = int(lines[1].strip())
    courier_capacity = list(map(int, lines[2].strip().split()))
    load_size = list(map(int, lines[3].strip().split()))
    
    dist_matrix = []
    for line in lines[4:]:
        row = list(map(int, line.strip().split()))
        dist_matrix.append(row)
    
    with open(dzn_file, 'w') as f:
        f.write(f"num_couriers = {num_couriers};\n")
        f.write(f"num_load = {num_load};\n")
        f.write(f"courier_capacity = {courier_capacity};\n")
        f.write(f"load_size = {load_size};\n")
        f.write("distance = [| ") 
        for i, row in enumerate(dist_matrix):
            f.write(", ".join(map(str, row)))
            if i < len(dist_matrix) - 1:
                f.write(",\n  | ") 
            else:
                f.write(" |];\n")  

def solve_model(instance_name, model_file, solver_str, timeout):
    model = Model(model_file)
    solver = Solver.lookup(solver_str)
    
    dzn_file_path = f"cp/converted_Instances/{instance_name}.dzn"
    
    num_couriers, num_load, courier_capacity, load_size, dist_matrix = None, None, None, None, []

    with open(dzn_file_path, 'r') as data_file:
        lines = data_file.readlines()
    
    reading_distance = False
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("num_couriers"):
            num_couriers = int(line.split('=')[1].strip(';').strip())
        elif line.startswith("num_load"):
            num_load = int(line.split('=')[1].strip(';').strip())
        elif line.startswith("courier_capacity"):
            capacity_str = line.split('=')[1].strip(';').strip()
            courier_capacity = list(map(int, capacity_str.strip('[]').replace(',', ' ').split()))
        elif line.startswith("load_size"):
            size_str = line.split('=')[1].strip(';').strip()
            load_size = list(map(int, size_str.strip('[]').replace(',', ' ').split()))
        elif line.startswith("distance"):
            reading_distance = True
            continue
        elif reading_distance:
            if line.endswith("];"):
                reading_distance = False
                line = line[:-2].strip()  
            elif line.endswith("|];"):
                line = line[:-3].strip()  
            elif line == "|":
                continue 
            
            row = line.strip().strip('|').strip()
            
            if row: 
                row = row.replace(',', '').strip()  
                if row:
                    try:
                        dist_matrix.append(list(map(int, row.split())))
                    except ValueError as e:
                        print(f"Error parsing row: '{row}'. Exception: {e}")
    
    #just error handling
    num_rows = len(dist_matrix)
    if num_rows > 0:
        num_cols = len(dist_matrix[0])
        if num_rows != num_cols:
            raise ValueError(f"Matrix is not square: {num_rows}x{num_cols}. Expected {num_couriers + 1}x{num_couriers + 1}.")
    else:
        raise ValueError("Distance matrix is empty.")

    dist_matrix = np.array(dist_matrix)

    inst = Instance(solver, model)
    inst["num_couriers"] = num_couriers
    inst["num_load"] = num_load
    inst["courier_capacity"] = courier_capacity
    inst["load_size"] = load_size
    inst["distance"] = dist_matrix

    start_time = datetime.datetime.now()
    result = inst.solve(timeout=timeout)
    end_time = datetime.datetime.now()

    elapsed_time_ms = (end_time - start_time).total_seconds() * 1000  
    elapsed_time_ms = round(elapsed_time_ms)  
    print(f"Elapsed Time: {elapsed_time_ms} ms")  
    return result, num_couriers, num_load, elapsed_time_ms


def get_results(result, num_couriers, num_load):
    result_dict = {"time": 0, "optimal": False, "obj": None, "sol": []}

    if result.solution:
        try:
            objective_str = str(result.solution).split("objective=")
            if len(objective_str) > 1:
                objective_str = objective_str[1].split(",")[0].strip()
                result_dict["obj"] = int(float(objective_str))

            if "load_assigned=" in str(result.solution):
                delivery_str = str(result.solution).split("load_assigned=")[1]
                delivery_str = delivery_str.split(", total_distance=")[0].strip("[]\n")
                delivery_list = delivery_str.split("], [")
                delivery_list = [list(map(int, x.strip("[]").split(", "))) for x in delivery_list]
                result_dict["sol"] = delivery_list

            if result.status == result.status.OPTIMAL_SOLUTION:
                result_dict["optimal"] = True
        except Exception as e:
            print(f"Error parsing result: {e}")
    
    return result_dict

dat_directory = 'instances'
dzn_directory = 'converted_instances'
result_directory = 'results'

if not os.path.exists(dzn_directory):
    os.makedirs(dzn_directory)
if not os.path.exists(result_directory):
    os.makedirs(result_directory)

instance_name = 'inst01'
# dat_file_path = os.path.join(dat_directory, f"{instance_name}.dat")
# dzn_file_path = os.path.join(dzn_directory, f"{instance_name}.dzn")
# convert_dat_to_dzn(dat_file_path, dzn_file_path)

model_file = "cp/fixed_models/model.mzn"
solver_str = "gecode"
timeout = datetime.timedelta(minutes=5)

def main():
    try:
        result, num_couriers, num_load, elapsed_time_ms = solve_model(instance_name, model_file, solver_str, timeout)
        result_dict = get_results(result, num_couriers, num_load)

        output = {
            solver_str: {
                "time": elapsed_time_ms,
                "optimal": result_dict["optimal"],
                "obj": result_dict["obj"],
                "sol": result_dict["sol"]
            }
        }
    except Exception as e:
        print(f"Error processing instance {instance_name}: {e}")
        print(Exception)
        output = {
            solver_str: {
                "time": 0,
                "optimal": False,
                "obj": None,
                "sol": None
            }
        }

    with open(f"{result_directory}/{instance_name}.json", "w") as file:
        json.dump(output, file, indent=3)

if __name__ == "__main__":
    main()
