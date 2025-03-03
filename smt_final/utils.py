import os
import json

def read_dat_file(filename):
    """
    Reads a .dat file and parses its contents into specified variables.

    Parameters:
        filename (str): The path to the .dat file.

    Returns:
        tuple: A tuple containing:
            - num_couriers (int)
            - num_load (int)
            - courier_capacity (list of int)
            - load_size (list of int)
            - distance (list of lists of int)
    """
    with open(filename, 'r') as file:
        # Read all lines and remove any leading/trailing whitespace
        lines = [line.strip() for line in file if line.strip()]
    
    # Ensure there are enough lines to parse
    if len(lines) < 4:
        raise ValueError("The file does not contain enough lines to parse the required variables.")
    
    # Parse the first four lines
    try:
        num_couriers = int(lines[0])
        num_load = int(lines[1])
        courier_capacity = list(map(int, lines[2].split()))
        load_size = list(map(int, lines[3].split()))
    except ValueError as e:
        raise ValueError(f"Error parsing the first four lines: {e}")
    
    # Parse the distance matrix
    distance = []
    for idx, line in enumerate(lines[4:], start=5):
        try:
            row = list(map(int, line.split()))
            distance.append(row)
        except ValueError as e:
            raise ValueError(f"Error parsing line {idx} of the distance matrix: {e}")
    
    return num_couriers, num_load, courier_capacity, load_size, distance

def compute_bounds(D_matrix, m, n):

    depot_index = n  # Assuming the depot is at index n (last row/column)

    # Compute lower bound: Maximum round-trip distance to/from the depot
    lower_bound = max(D_matrix[depot_index][i] + D_matrix[i][depot_index] for i in range(1, n+1))

    # Compute the sum of distances for i ranging from 1 to floor(n/m) + 1
    num_terms = min(n, (n // m) + 1)  # Ensure we don’t go out of bounds
    sum_distances = sum(D_matrix[i][i+1] for i in range(1, num_terms))

    # Compute the upper bound by adding the lower bound
    upper_bound = sum_distances + lower_bound

    return lower_bound, upper_bound

def save_json(data_dict, solver_name, file_name, base_path):

    # Ensure the base path exists
    try:
        os.makedirs(base_path, exist_ok=True)
    except Exception as e:
        print(f"Failed to create directory '{base_path}': {e}")
        raise
    
    # Construct the full file path
    file_path = os.path.join(base_path, file_name)

    # Load existing data if the file exists
    existing_data = {}
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        except (json.JSONDecodeError, IOError):
            print(f"Warning: Unable to read existing JSON file '{file_path}', starting fresh.")
    
    # Overwrite or add the solver entry
    existing_data[solver_name] = data_dict

    # Save the updated data back to the file
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=4)
        print(f"Data for solver '{solver_name}' has been stored in '{file_path}'.")
    except IOError as e:
        print(f"An error occurred while writing to the file '{file_path}': {e}")
        raise

def follow_loop(start, arcs_used):
            route = [start]
            current = start
            while True:
                # Find next 'v' if (current, v) is in arcs_used
                next_vs = [v for (u, v) in arcs_used if u == current]
                if not next_vs:
                    # No continuation from current
                    break
                # Pick the first arc (assuming exactly one next node due to constraints)
                v = next_vs[0]
                route.append(v)
                arcs_used.remove((current, v))
                current = v
                if current == start:
                    # Loop closed
                    break
            return route
