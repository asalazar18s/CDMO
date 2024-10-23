import numpy as np
import time
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpBinary, PULP_CBC_CMD

class MCP:
    def __init__(self, distance, num_couriers, max_capacities, load_sizes):
        self.distance = distance
        self.n = len(distance)  # number of nodes (total load + depot)
        self.m = num_couriers
        self.max_capacities = max_capacities
        self.load_sizes = load_sizes
        self.problem = LpProblem('VRP', LpMinimize)

    def solve(self):
        start_time = time.time()
        x = {}  # decision binary variables: x[i,j,k] = 1 if courier k goes from node i to j
        u = {}  # variables for MTZ subtour elimination
    
        for i in range(self.n):
            for j in range(self.n):
                for k in range(self.m):
                    if i != j:
                        x[i, j, k] = LpVariable(f'x_{i}_{j}_{k}', cat=LpBinary)
        
        # MTZ variables
        for i in range(1, self.n):
            for k in range(self.m):
                u[i, k] = LpVariable(f'u_{i}_{k}', lowBound=0, upBound=self.n - 1)

        # objective function
        total_distance = lpSum(self.distance[i][j] * x[i, j, k] for i in range(self.n) for j in range(self.n) for k in range(self.m) if i != j)
        self.problem += total_distance

        # constraints =======================================================================================================================
        
        # each load must go to one courier and be picked up only once
        for j in range(1, self.n):
            self.problem += lpSum(x[i, j, k] for i in range(self.n) for k in range(self.m) if i != j) == 1
        
        # each load must be assigned to some courier
        for j in range(1, self.n):
            self.problem += lpSum(x[i, j, k] for i in range(self.n) for k in range(self.m) if i != j) >= 1
        
        # courier starts and ends at the origin point (depot)
        for k in range(self.m):
            self.problem += lpSum(x[0, j, k] for j in range(1, self.n)) == 1
            self.problem += lpSum(x[i, 0, k] for i in range(1, self.n)) == 1
        
        # load capacity constraint for each courier
        for k in range(self.m):
            self.problem += lpSum(self.load_sizes[j-1] * x[i, j, k] for i in range(self.n) for j in range(1, self.n) if i != j) <= self.max_capacities[k]

        # subtour elimination using MTZ constraint
        for i in range(1, self.n):
            for j in range(1, self.n):
                for k in range(self.m):
                    if i != j:
                        self.problem += u[i, k] - u[j, k] + (self.n - 1) * x[i, j, k] <= self.n - 2
        
        # each courier must have at least one assignment
        for k in range(self.m):
            self.problem += lpSum(x[0, j, k] for j in range(1, self.n)) >= 1  # Each courier should at least serve one load

        # symmetry Breaking Constraint
        for c in range(self.m - 1):
            if self.max_capacities[c] == self.max_capacities[c + 1]:  # Check if capacities are equal
                self.problem += lpSum(x[0, j, c] for j in range(1, self.n)) >= lpSum(x[0, j, c + 1] for j in range(1, self.n))  # Ensure loads assigned to courier c are less than or equal to those assigned to courier c + 1


        # Solve the problem
        self.problem.solve(PULP_CBC_CMD())

        time_taken = time.time() - start_time

        # Output =======================================================================================================================
        if self.problem.status == 1:
            return self.get_solution(x, time_taken, True)
        else:
            return self.get_solution(x, time_taken, False)
        
    def get_solution(self, x, time_taken, optimal):
        routes = []
        for k in range(self.m):
            route = []
            for i in range(self.n):
                for j in range(self.n):
                    if i != j and x[i, j, k].varValue > 0.5:
                        route.append(j)
            routes.append([node for node in route if node != 0])
        
        solution = {
            'time': round(time_taken, 2),
            'optimal': optimal,
            'obj': round(self.problem.objective.value(), 2),
            'sol': routes          
        }

        return solution
    
# Example run for instance 01
if __name__ == "__main__":
    # Instance 02 data
    num_couriers = 6
    num_load = 9
    courier_capacity = [190, 185, 185, 190, 195, 185]
    load_size = [11, 11, 23, 16, 2, 1, 24, 14, 20]
    
    distance = [
        [0, 199, 119, 28, 179, 77, 145, 61, 123, 87],
        [199, 0, 81, 206, 38, 122, 55, 138, 76, 113],
        [119, 81, 0, 126, 69, 121, 26, 117, 91, 32],
        [28, 206, 126, 0, 186, 84, 152, 68, 130, 94],
        [169, 38, 79, 176, 0, 92, 58, 108, 46, 98],
        [77, 122, 121, 84, 102, 0, 100, 16, 46, 96],
        [145, 55, 26, 152, 58, 100, 0, 91, 70, 58],
        [61, 138, 113, 68, 118, 16, 91, 0, 62, 87],
        [123, 76, 91, 130, 56, 46, 70, 62, 0, 66],
        [87, 113, 32, 94, 94, 96, 58, 87, 66, 0]
    ]
    
    mcp_solver = MCP(distance, num_couriers, courier_capacity, load_size)
    solution = mcp_solver.solve()

    print(solution)
