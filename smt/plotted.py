import matplotlib.pyplot as plt
from z3 import Optimize, Int, Sum
import random

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

# Random coordinates for visualization
coordinates = [(random.randint(0, 10), random.randint(0, 10)) for _ in range(num_load)]  # Load points
origin_coord = (5, 5)  # Fixed origin point
coordinates.append(origin_coord)  # Add origin to the coordinates

# Z3 Optimizer
optimizer = Optimize()

# Decision variables
x = [[Int(f"x_{i}_{j}") for j in range(num_load)] for i in range(num_couriers)]  # Load assignment
total_distance = Int("total_distance")  # Total distance traveled by all couriers

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

# 4. Total distance calculation
courier_distances = []
for i in range(num_couriers):
    courier_distance = Sum([x[i][j] * distance[origin][j] for j in range(num_load)]) + \
                       Sum([x[i][j] * x[i][k] * distance[j][k] for j in range(num_load) for k in range(num_load)])
    courier_distances.append(courier_distance)

# Total distance across all couriers
optimizer.add(total_distance == Sum(courier_distances))

# Objective: Minimize the total distance
optimizer.minimize(total_distance)

# Solve the problem
if optimizer.check().__str__() == "sat":
    model = optimizer.model()
    print("Solution found:")
    routes = []
    for i in range(num_couriers):
        assigned_loads = [j for j in range(num_load) if model.evaluate(x[i][j]).as_long() == 1]
        courier_distance = model.evaluate(courier_distances[i]).as_long()
        routes.append(assigned_loads)
        print(f"Courier {i + 1}: Loads {assigned_loads}, Distance: {courier_distance}")
    print(f"Total Distance: {model.evaluate(total_distance).as_long()}")

    # Visualization
    colors = ['blue', 'orange']  # Colors for each courier
    plt.figure(figsize=(8, 8))

    # Plot each courier's route
    for i, route in enumerate(routes):
        route_coords = [origin_coord] + [coordinates[j] for j in route] + [origin_coord]  # Include origin
        x_coords, y_coords = zip(*route_coords)
        plt.plot(x_coords, y_coords, marker='o', label=f"Courier {i + 1}", color=colors[i])
        for idx, (x, y) in enumerate(route_coords[1:-1]):  # Add labels for load indices
            plt.text(x, y, f"{route[idx]}")

    # Plot origin
    plt.scatter(*origin_coord, color='red', s=100, label="Origin", zorder=5)

    # Final plot settings
    plt.title("Courier Routes")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.legend()
    plt.grid()
    plt.show()
else:
    print("No solution exists.")
