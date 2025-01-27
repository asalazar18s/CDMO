from z3 import Optimize, Int, Sum

# Input Data
num_couriers = 2
num_load = 6
courier_capacity = [15, 10]
load_size = [3, 2, 6, 5, 4, 4]
distance = [
    [0, 3, 4, 5, 6, 6, 2],
    [3, 0, 1, 4, 5, 7, 3],
    [4, 1, 0, 5, 6, 6, 4],
    [5, 4, 5, 0, 3, 3, 2],
    [6, 5, 6, 3, 0, 2, 4],
    [6, 7, 6, 3, 2, 0, 4],
    [2, 3, 4, 3, 4, 4, 0]
]
origin = num_load  # Origin index in the distance matrix (last row/column)

# Z3 Optimizer
optimizer = Optimize()

# Decision variables
x = [[Int(f"x_{i}_{j}") for j in range(num_load)] for i in range(num_couriers)]  # Load assignment
max_distance = Int("max_distance")  # Maximum distance traveled by any courier

# Constraints
# 1. Each load must be assigned to exactly one courier
for j in range(num_load):
    optimizer.add(Sum([x[i][j] for i in range(num_couriers)]) == 1)

# 2. Each courier's total load must not exceed its capacity
for i in range(num_couriers):
    optimizer.add(Sum([x[i][j] * load_size[j] for j in range(num_load)]) <= courier_capacity[i])

# 3. Binary constraints for decision variables
for i in range(num_couriers):
    for j in range(num_load):
        optimizer.add(x[i][j] >= 0, x[i][j] <= 1)

# 4. Distance calculation
for i in range(num_couriers):
    total_distance = Sum([x[i][j] * distance[origin][j] for j in range(num_load)]) + \
                     Sum([x[i][j] * x[i][k] * distance[j][k] for j in range(num_load) for k in range(num_load)])
    optimizer.add(total_distance <= max_distance)

# Objective: Minimize the maximum distance traveled
optimizer.add(max_distance >= 0)
optimizer.minimize(max_distance)

# Solve the problem
if optimizer.check().__str__() == "sat":
    model = optimizer.model()
    print("Solution found:")
    for i in range(num_couriers):
        assigned_loads = [j for j in range(num_load) if model.evaluate(x[i][j]).as_long() == 1]
        total_distance = sum(distance[origin][j] for j in assigned_loads) + \
                         sum(distance[j][k] for j in assigned_loads for k in assigned_loads if j != k)
        print(f"Courier {i + 1}: Loads {assigned_loads}, Distance: {total_distance}")
    print(f"Maximum Distance: {model.evaluate(max_distance).as_long()}")
else:
    print("No solution exists.")
