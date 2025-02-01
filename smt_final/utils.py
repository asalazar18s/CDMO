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

def build_single_route_from_origin(i, origin, arcs_used):
    """
    Follow arcs starting from 'origin' until we return to 'origin'
    or can no longer proceed. Returns the route as a list of nodes.
    """
    route = [origin]
    current = origin
    while True:
        # Find the next 'v' if (current, v) is in arcs_used
        next_vs = [v_ for (u_, v_) in arcs_used if u_ == current]
        if not next_vs:
            # No continuation from current
            break
        v_ = next_vs[0]  # typically exactly 1 in a well-formed route
        route.append(v_)
        arcs_used.remove((current, v_))
        current = v_
        if current == origin:
            # we made it back to origin => route complete
            break
    return route

def rotate_loop_to_origin(loop, origin):
    if origin in loop:
        idx = loop.index(origin)
        # rotate so that loop[idx] becomes the first element
        loop = loop[idx:] + loop[:idx]
    return loop

def reconstruct_single_loop(i, origin, arcs_used):
    # Start from origin, follow arcs until we return to origin
    route = [origin]
    current = origin
    while True:
        next_vs = [v for (u,v) in arcs_used if u == current]
        if not next_vs:  # no continuation
            break
        v = next_vs[0]  # typically exactly 1
        route.append(v)
        arcs_used.remove((current, v))
        current = v
        if current == origin:
            # route is complete
            break
    return route

# Compute lower and upper bounds
def compute_bounds(D_matrix, ITEMS, m, implied_constraint=False):
    n = len(D_matrix) - 1  # Assuming origin is indexed at n
    # Compute lower bound
    lower_bound = max([D_matrix[n][j] + D_matrix[j][n] for j in ITEMS])
    
    # Compute maximum distances per node (excluding origin)
    max_distances = [max(D_matrix[i][:-1]) for i in range(n)]
    max_distances.sort()
    
    if implied_constraint:
        upper_bound = sum(max_distances[m:]) + max(D_matrix[n]) + max([D_matrix[j][n] for j in range(n)])
    else:
        upper_bound = sum(max_distances[1:]) + max(D_matrix[n]) + max([D_matrix[j][n] for j in range(n)])
    
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
