import os

def convert_file(dat_file, dzn_file):
    # Open the .dat file for reading
    with open(dat_file, 'r') as f:
        lines = f.readlines()
    
    # Read the number of couriers and loads from the file
    num_couriers = int(lines[0].strip())
    num_load = int(lines[1].strip())
    
    # Read courier capacities and load sizes
    courier_capacity = list(map(int, lines[2].strip().split()))
    load_size = list(map(int, lines[3].strip().split()))
    
    # Read the distance matrix from the file
    dist_matrix = []
    for line in lines[4:]:
        row = list(map(int, line.strip().split()))
        dist_matrix.append(row)
    
    # Open the .dzn file for writing
    with open(dzn_file, 'w') as f:
        # Write the number of couriers and loads
        f.write(f"num_couriers = {num_couriers};\n")
        f.write(f"num_load = {num_load};\n")

        # Write the courier capacities and load sizes
        f.write(f"courier_capacity = {courier_capacity};\n")
        f.write(f"load_size = {load_size};\n")
        
        # Write the distance matrix in .dzn format
        f.write("distance = [| ")  # Start the matrix definition
        for i, row in enumerate(dist_matrix):
            f.write(", ".join(map(str, row)))  # Write each row
            if i < len(dist_matrix) - 1:
                f.write(",\n  | ")  # Continue with the next row
            else:
                f.write(" |];\n")  # End the matrix definition


# Directories
dat_directory = 'instances'
dzn_directory = 'converted_instance'

# Create directories if they don't exist
os.makedirs(dat_directory, exist_ok=True)
os.makedirs(dzn_directory, exist_ok=True)

instance_name = 'inst01'
dat_file_path = os.path.join(dat_directory, f"{instance_name}.dat")
dzn_file_path = os.path.join(dzn_directory, f"{instance_name}.dzn")

# Check if the dat file exists before conversion
if os.path.exists(dat_file_path):
    convert_file(dat_file_path, dzn_file_path)
else:
    print(f"Error: The .dat file '{dat_file_path}' does not exist.")