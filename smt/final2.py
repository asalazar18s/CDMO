from z3 import *
from utils import utils_SMT 

# Fetch problem parameters
num_couriers, num_load, courier_capacity, load_size, distance = utils_SMT.read_dat_file("Instances/inst01.dat")

# Initialize the Z3 Solver
solver = Solver()

# Step 1: Define Assignment Variables as Integers (0 or 1)
assign = [
    [Int(f"assign_courier_{i}_load_{j}") for j in range(num_load)]
    for i in range(num_couriers)
]

# Add constraints that assignment variables are binary
for i in range(num_couriers):
    for j in range(num_load):
        solver.add(Or(assign[i][j] == 0, assign[i][j] == 1))

# Add Exclusive Assignment Constraints
for j in range(num_load):
    # For each load j, exactly one courier is assigned
    solver.add(Sum([assign[i][j] for i in range(num_couriers)]) == 1)

# Add Capacity Constraints
for i in range(num_couriers):
    # Calculate the total load for courier i
    total_load = Sum([assign[i][j] * load_size[j] for j in range(num_load)])
    # Add the constraint that total_load <= courier_capacity[i]
    solver.add(total_load <= courier_capacity[i])

# Step 2: Define Routing Variables (Order Variables)
order = [
    [Int(f"order_courier_{i}_load_{j}") for j in range(num_load)]
    for i in range(num_couriers)
]

# Add Constraints for Order Variables
for i in range(num_couriers):
    for j in range(num_load):
        # If load j is assigned to courier i, set 1 <= order[i][j] <= num_load
        # Else, set order[i][j] == 0
        solver.add(
            If(assign[i][j] == 1,
               And(order[i][j] >= 1, order[i][j] <= num_load),
               order[i][j] == 0)
        )

# Step 3: Implement Subtour Elimination using MTZ Constraints
# Define auxiliary variables for MTZ constraints
u = [
    [Int(f"u_courier_{i}_load_{j}") for j in range(num_load)]
    for i in range(num_couriers)
]

for i in range(num_couriers):
    for j in range(num_load):
        if courier_capacity[i] >= load_size[j]:
            # If load j is assigned to courier i, set 1 <= u[i][j] <= num_load
            # Else, set u[i][j] == 0
            solver.add(
                If(assign[i][j] == 1,
                   And(u[i][j] >= 1, u[i][j] <= num_load),
                   u[i][j] == 0)
            )
        else:
            # If courier i cannot carry load j, ensure assign[i][j] == 0
            solver.add(assign[i][j] == 0)
    
    for j in range(num_load):
        for k in range(num_load):
            if j != k:
                # Apply MTZ constraints only if both loads are assigned to courier i
                solver.add(
                    Implies(
                        And(assign[i][j] == 1, assign[i][k] == 1, order[i][j] < order[i][k], order[i][j] + 1 == order[i][k]),
                        u[i][j] < u[i][k]
                    )
                )

# Step 4: Calculate Total Distances
# Define total distance variables
total_distance = [Int(f"total_distance_courier_{i}") for i in range(num_couriers)]

for i in range(num_couriers):
    # Initialize list to hold distance terms
    distance_terms = []
    
    # Distance from Origin to First Load
    for j in range(num_load):
        distance_terms.append(
            If(assign[i][j] == 1,
               distance[num_load][j],
               0)
        )
    
    # Distances between Loads based on Order
    for j in range(num_load):
        for k in range(num_load):
            if j != k:
                # Add distance[j][k] if load j precedes load k in order and is directly before
                distance_terms.append(
                    If(And(assign[i][j] == 1, assign[i][k] == 1, order[i][j] < order[i][k], order[i][j] + 1 == order[i][k]),
                       distance[j][k],
                       0)
                )
    
    # Distance from Last Load Back to Origin
    for j in range(num_load):
        distance_terms.append(
            If(assign[i][j] == 1,
               distance[j][num_load],
               0)
        )
    
    # Define total_distance[i] as the sum of all distance terms
    solver.add(total_distance[i] == Sum(distance_terms))

# Step 5: Integrate Routing into the Existing Model with Optimization
# Switch to Optimize solver for handling optimization objectives
optimizer = Optimize()

# Transfer all existing constraints from 'solver' to 'optimizer'
optimizer.add(solver.assertions())

# Define max_distance variable
max_distance = Int("max_distance")

# Add constraints that max_distance >= total_distance[i] for all couriers
for i in range(num_couriers):
    optimizer.add(max_distance >= total_distance[i])

# Set the optimization objective to minimize max_distance
optimizer.minimize(max_distance)

# Step 6: Check Satisfiability and Extract the Model with Tour Paths
if optimizer.check() == sat:
    model = optimizer.model()
    assignment_result = [[] for _ in range(num_couriers)]
    order_result = [[] for _ in range(num_couriers)]
    total_distances = [0 for _ in range(num_couriers)]
    
    for i in range(num_couriers):
        for j in range(num_load):
            # Evaluate the assignment variable
            assign_val = model.evaluate(assign[i][j]).as_long()
            if assign_val == 1:
                assignment_result[i].append(j)
                # Evaluate the order variable
                order_val = model.evaluate(order[i][j]).as_long()
                order_result[i].append((order_val, j))
    
    # Display the assignments with total loads and distances
    for i in range(num_couriers):
        if not order_result[i]:
            # If no loads are assigned to the courier
            print(f"Courier {i + 1} has no assigned loads.")
            print(f"Courier {i + 1} Tour Path: Origin → Origin")
            print(f"Courier {i + 1} Total Distance: 0 units\n")
            continue
        
        # Sort the loads based on their order
        sorted_loads = sorted(order_result[i], key=lambda x: x[0])
        # Extract load indices in order
        ordered_loads = [j + 1 for (_, j) in sorted_loads]  # Convert to 1-based indexing
        
        # Construct the tour path
        tour = ["Origin"]
        for load in ordered_loads:
            tour.append(f"Load {load}")
        tour.append("Origin")
        tour_path = " → ".join(tour)
        
        # Retrieve total distance from the model
        route_distance = model.evaluate(total_distance[i]).as_long()
        # Calculate total load
        total_load = sum([load_size[j - 1] for j in ordered_loads])
        
        print(f"Courier {i + 1} is assigned to Loads: {ordered_loads} with Total Load: {total_load}")
        print(f"Courier {i + 1} Tour Path: {tour_path}")
        print(f"Courier {i + 1} Total Distance: {route_distance} units\n")
    
    # Display the maximum distance
    max_dist = model.evaluate(max_distance).as_long()
    print(f"Maximum Distance Traveled by Any Courier: {max_dist} units")
else:
    print("No solution found.")
