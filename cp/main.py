import os
import numpy as np
from minizinc import Instance, Model, Solver
import datetime
import json

def convert_dat_to_dzn(dat_file, dzn_file):
    with open(dat_file, 'r') as f:
        lines = f.readlines()
    
    # Parse data from .dat file
    num_couriers = int(lines[0].strip())
    num_load = int(lines[1].strip())
    courier_capacity = list(map(int, lines[2].strip().split()))
    load_size = list(map(int, lines[3].strip().split()))
    
    # Read the distance matrix
    dist_matrix = []
    for line in lines[4:]:
        row = list(map(int, line.strip().split()))
        dist_matrix.append(row)
    
    # Convert to a numpy array for easier manipulation
    dist_matrix = np.array(dist_matrix)
    
    # Create .dzn formatted data
    with open(dzn_file, 'w') as f:
        f.write(f"num_couriers = {num_couriers};\n")
        f.write(f"num_load = {num_load};\n")
        f.write(f"courier_capacity = {courier_capacity};\n")
        f.write(f"load_size = {load_size};\n")
        
        # Write distance matrix in .dzn format
        f.write("distance = [\n")
        for row in dist_matrix:
            f.write("  | " + " ".join(map(str, row)) + " |\n")
        f.write("];\n")


def solve_model(instance_name, model_file, solver_str, timeout):
    model = Model(model_file)
    solver = Solver.lookup(solver_str)
    
    # Path to the converted .dzn file
    dzn_file_path = f"Converted_Instances/{instance_name}.dzn"
    
    # Initialize variables
    num_couriers = None
    num_load = None
    courier_capacity = None
    load_size = None
    dist_matrix = []

    with open(dzn_file_path, 'r') as data_file:
        lines = data_file.readlines()
    
    # Variables to track parsing state
    reading_distance = False
    
    for line in lines:
        line = line.strip()
        
        if line.startswith("num_couriers"):
            num_couriers = int(line.split('=')[1].strip(';').strip())
        elif line.startswith("num_load"):
            num_load = int(line.split('=')[1].strip(';').strip())
        elif line.startswith("courier_capacity"):
            capacity_str = line.split('=')[1].strip(';').strip()
            # Remove unwanted characters like commas and brackets
            courier_capacity = list(map(int, capacity_str.strip('[]').replace(',', ' ').split()))
        elif line.startswith("load_size"):
            size_str = line.split('=')[1].strip(';').strip()
            # Remove unwanted characters like commas and brackets
            load_size = list(map(int, size_str.strip('[]').replace(',', ' ').split()))
        elif line.startswith("distance"):
            reading_distance = True
            # Skip the opening line of the matrix
            continue
        elif reading_distance:
            if line == "];":
                # End of distance matrix
                reading_distance = False
                break
            # Process matrix row
            row = line.strip().strip('|').split()
            if row:
                dist_matrix.append(list(map(int, row)))
    
    dist_matrix = np.array(dist_matrix)

    # Check parsed values
    print(f"Num Couriers: {num_couriers}")
    print(f"Num Load: {num_load}")
    print(f"Courier Capacity: {courier_capacity}")
    print(f"Load Size: {load_size}")
    print(f"Distance Matrix: \n{dist_matrix}")

    # Transform Model into an instance
    inst = Instance(solver, model)
    inst["num_couriers"] = num_couriers
    inst["num_load"] = num_load
    inst["courier_capacity"] = courier_capacity
    inst["load_size"] = load_size
    inst["distance"] = dist_matrix

    # Solve the model
    result = inst.solve(timeout=timeout)
    return result, num_couriers, num_load




def get_results(result, num_couriers, num_load):
    lines = str(result.solution).split("\n")
    try: 
        objective = float(lines[0])
    except: 
        objective = lines[0]
    if type(objective) is float:
        objective = int(objective)

    if len(lines) > 1:
        delivery_order = lines[1].strip("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ[]= ;\n").replace(",","")
        delivery_order = list(delivery_order.split(' '))
        delivery_order = [int(i) for i in delivery_order]
        delivery_order = np.array(delivery_order).reshape(num_load + 2, num_couriers).T 

        sol = list()
        for i in range(num_couriers):
            c_sol = list()
            for j in range(num_load + 2):
                if delivery_order[i][j] != 0:
                    c_sol.append(int(delivery_order[i][j]))
            sol.append(c_sol)
    else:
        sol = None

    status = (result.status == result.status.OPTIMAL_SOLUTION)
    runTime = int(result.statistics['solveTime'].total_seconds()) if status else 0

    return objective, sol, runTime, status

# Directories
dat_directory = 'Instances'
dzn_directory = 'Converted_Instances'
result_directory = 'results'

# Ensure directories exist
if not os.path.exists(dzn_directory):
    os.makedirs(dzn_directory)
if not os.path.exists(result_directory):
    os.makedirs(result_directory)

# Convert .dat files to .dzn
for dat_file in os.listdir(dat_directory):
    if dat_file.endswith(".dat"):
        dat_file_path = os.path.join(dat_directory, dat_file)
        dzn_file_name = os.path.splitext(dat_file)[0] + '.dzn'
        dzn_file_path = os.path.join(dzn_directory, dzn_file_name)
        convert_dat_to_dzn(dat_file_path, dzn_file_path)

# Define the model file
model_file = "model.mzn"

# Solver configuration
solver_str = "gecode"  # Change to your desired solver if needed
timeout = datetime.timedelta(minutes=5)  # Set the timeout as needed

def main():
    for dzn_file in os.listdir(dzn_directory):
        if dzn_file.endswith(".dzn"):
            instance_name = os.path.splitext(dzn_file)[0]
            print(f'Processing instance {instance_name}')
            try:
                result, num_couriers, num_load = solve_model(instance_name, model_file, solver_str, timeout)
                obj, solution, runTime, status = get_results(result, num_couriers, num_load)

                # JSON output
                instance_result = {
                    "time": runTime,
                    "optimal": status,
                    "obj": obj,
                    "solution": solution
                }
            except Exception as e:
                print(f"Error processing instance {instance_name}: {e}")
                instance_result = {
                    "time": 0,
                    "optimal": False,
                    "obj": None,
                    "solution": None
                }

            with open(f"{result_directory}/{instance_name}.json", "w") as file:
                json.dump(instance_result, file, indent=3)

if __name__ == "__main__":
    main()
