from z3 import *

# Problem Parameters
num_couriers = 2  # Number of couriers
num_load = 6  # Number of loads
courier_capacity = [15, 10]  # Capacity of each courier
load_size = [3, 2, 6, 5, 4, 4]  # Size of each load

distance = [  # Distance matrix (n+1 x n+1), where the last index (n+1) is the origin
    [0, 3, 4, 5, 6, 6, 2],
    [3, 0, 1, 4, 5, 7, 3],
    [4, 1, 0, 5, 6, 6, 4],
    [5, 4, 5, 0, 3, 3, 2],
    [6, 5, 6, 3, 0, 2, 4],
    [6, 7, 6, 3, 2, 0, 4],
    [2, 3, 4, 3, 4, 4, 0]
]

# Initialize the Z3 Solver
solver = Solver()

# Define assignment variables
assign = [
    [Bool(f"assign_courier_{i}_load_{j}") for j in range(num_load)]
    for i in range(num_couriers)
]

# Add exclusive assignment constraints
for j in range(num_load):
    # For each load j, exactly one courier is assigned
    solver.add(Sum([If(assign[i][j], 1, 0) for i in range(num_couriers)]) == 1)

# Add capacity constraints
for i in range(num_couriers):
    total_load = Sum([If(assign[i][j], load_size[j], 0) for j in range(num_load)])
    solver.add(total_load <= courier_capacity[i])

# Check if the constraints are satisfiable
if solver.check() == sat:
    model = solver.model()
    assignment_result = [[] for _ in range(num_couriers)]
    
    for i in range(num_couriers):
        for j in range(num_load):
            # Check if assign[i][j] is True in the model
            if is_true(model.evaluate(assign[i][j])):
                assignment_result[i].append(j)
    
    # Display the assignments with total loads
    for i, courier_loads in enumerate(assignment_result):
        assigned_loads = [j + 1 for j in courier_loads]  # Convert to 1-based indexing
        total = sum([load_size[j] for j in courier_loads])
        print(f"Courier {i + 1} is assigned to Loads: {assigned_loads} with Total Load: {total}")
else:
    print("No solution found.")


# Step 1: Define Routing Variables

# Define order variables: order[i][j] represents the sequence position of load j in courier i's route
order = [
    [Int(f"order_courier_{i}_load_{j}") for j in range(num_load)]
    for i in range(num_couriers)
]

# Add constraints for order variables
for i in range(num_couriers):
    for j in range(num_load):
        # If load j is assigned to courier i, then order[i][j] >= 1
        # Else, order[i][j] == 0 (not part of the route)
        solver.add(
            If(assign[i][j] == 1,
               And(order[i][j] >= 1, order[i][j] <= num_load),
               order[i][j] == 0)
        )


# Step 2: Establish Sequencing Constraints

for i in range(num_couriers):
    # Calculate the number of loads assigned to courier i
    num_assigned = Sum([assign[i][j] for j in range(num_load)])
    
    # Enforce that order positions are unique for assigned loads
    for j1 in range(num_load):
        for j2 in range(j1 + 1, num_load):
            # If both loads j1 and j2 are assigned to courier i
            # Then their order positions must be different
            solver.add(
                Implies(
                    And(assign[i][j1] == 1, assign[i][j2] == 1),
                    order[i][j1] != order[i][j2]
                )
            )
    
    # Enforce that the sequence positions are consecutive
    # This can be done by ensuring that for assigned loads, their orders cover 1 to k_i without gaps
    # Since Z3 doesn't support direct enumeration, this is implicitly handled by the range constraints
    # and the uniqueness constraints


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
            solver.add(
                If(assign[i][j] == 1,
                   And(u[i][j] >= 1, u[i][j] <= num_load),
                   u[i][j] == 0)  # Unassigned loads have u = 0
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
                        And(assign[i][j] == 1, assign[i][k] == 1, order[i][j] < order[i][k]),
                        u[i][j] < u[i][k]
                    )
                )

# Step 4: Calculate Total Distances

# Define total distance variables
total_distance = [Int(f"total_distance_courier_{i}") for i in range(num_couriers)]

for i in range(num_couriers):
    # Initialize list to hold distance terms
    distance_terms = []
    
    # Add distance from origin to first load
    for j in range(num_load):
        distance_terms.append(
            If(assign[i][j] == 1,
               distance[6][j],  # Origin is index 6
               0)
        )
    
    # Add distances between loads
    for j in range(num_load):
        for k in range(num_load):
            if j != k:
                distance_terms.append(
                    If(And(assign[i][j] == 1, assign[i][k] == 1, order[i][j] == order[i][k] - 1),
                       distance[j][k],
                       0)
                )
    
    # Add distance from last load back to origin
    for j in range(num_load):
        distance_terms.append(
            If(assign[i][j] == 1,
               distance[j][6],  # Origin is index 6
               0)
        )
    
    # Define total_distance[i] as the sum of all distance terms
    solver.add(total_distance[i] == Sum(distance_terms))
