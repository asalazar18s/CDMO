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

# # Example usage:
# if __name__ == "__main__":
#     filename = "Instances/inst01.dat"  # Replace with your actual file path
#     try:
#         num_couriers, num_load, courier_capacity, load_size, distance = read_dat_file(filename)
#         print("Number of Couriers:", num_couriers)
#         print("Number of Loads:", num_load)
#         print("Courier Capacities:", courier_capacity)
#         print("Load Sizes:", load_size)
#         print("Distance Matrix:")
#         for row in distance:
#             print(row)
#     except Exception as e:
#         print(f"An error occurred: {e}")
