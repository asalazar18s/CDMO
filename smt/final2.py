from z3 import *

# # Problem Parameters
# num_couriers = 2  # Number of couriers
# num_load = 6      # Number of loads
# courier_capacity = [15, 10]  # Capacity of each courier
# load_size = [3, 2, 6, 5, 4, 4]  # Size of each load

# distance = [  # Distance matrix (7 x 7), where index 6 is the origin (Distribution Point 7)
#     [0, 3, 4, 5, 6, 6, 2],  # Distribution Point 1
#     [3, 0, 1, 4, 5, 7, 3],  # Distribution Point 2
#     [4, 1, 0, 5, 6, 6, 4],  # Distribution Point 3
#     [5, 4, 5, 0, 3, 3, 2],  # Distribution Point 4
#     [6, 5, 6, 3, 0, 2, 4],  # Distribution Point 5
#     [6, 7, 6, 3, 2, 0, 4],  # Distribution Point 6
#     [2, 3, 4, 3, 4, 4, 0]   # Origin (Distribution Point 7)
# ]

num_couriers = 6
num_load = 9
courier_capacity = [190, 185, 185, 190, 195, 185]
load_size = [11, 11, 23, 16, 2, 1, 24, 14, 20]
distance_flat = [ 0, 199, 119, 28, 179, 77, 145, 61, 123, 87,
   199, 0, 81, 206, 38, 122, 55, 138, 76, 113,
   119, 81, 0, 126, 69, 121, 26, 117, 91, 32,
   28, 206, 126, 0, 186, 84, 152, 68, 130, 94,
   169, 38, 79, 176, 0, 92, 58, 108, 46, 98,
   77, 122, 121, 84, 102, 0, 100, 16, 46, 96,
   145, 55, 26, 152, 58, 100, 0, 91, 70, 58,
   61, 138, 113, 68, 118, 16, 91, 0, 62, 87,
   123, 76, 91, 130, 56, 46, 70, 62, 0, 66,
   87, 113, 32, 94, 94, 96, 58, 87, 66, 0 ]

# Convert the flattened distance list into a 2D list (10x10)
distance = [distance_flat[i*10:(i+1)*10] for i in range(10)]

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
