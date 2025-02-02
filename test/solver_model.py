import pulp

def solve_multiple_couriers(m, n, D, l, s, solver, timeout=300 ):
    
    s.append(0)

    packages = list(range(n + 1))

    packages_no_base = packages[:-1]

    couriers = list(range(m))

    model = pulp.LpProblem("Multiple_Couriers", pulp.LpMinimize)

    
    y = [[[pulp.LpVariable(f"y_{c}_{p1}_{p2}", cat=pulp.LpBinary) for p2 in packages] for p1 in packages] for c in couriers]

    distances = [pulp.lpSum(D[p1][p2] * y[c][p1][p2] for p1 in packages for p2 in packages) for c in couriers]
    d_max = pulp.LpVariable("d_max", lowBound=0)
    model += d_max
    for c in couriers:
        model += d_max >= distances[c]

    for c in couriers:
        for p1 in packages:
            for p2 in packages:
                p3s = [p3 for p3 in packages if p3 == n or p1 == n or (p3 != p1 and p3 != p2)]
                incoming = pulp.lpSum(y[c][p3][p1] for p3 in p3s)
                model += incoming <= 1
                model += incoming >= y[c][p1][p2]
            model += y[c][p1][p1] == 0  # No self-loops
        model += pulp.lpSum(s[p1] * y[c][p1][p2] for p1 in packages for p2 in packages) <= l[c]

    for p in packages_no_base:
        model += pulp.lpSum(y[c][p][p2] for c in couriers for p2 in packages) == 1

    path_increment = [[pulp.LpVariable(f"path_increment_{c}_{p}", lowBound=0, upBound=n, cat=pulp.LpInteger) for p in packages] for c in couriers]
    for c in couriers:
        path_increment[c][n].setInitialValue(0)
        for p1 in packages:
            for p2 in packages_no_base:
                model += path_increment[c][p2] >= path_increment[c][p1] + 1 - n * (1 - y[c][p1][p2])
                model += path_increment[c][p2] <= path_increment[c][p1] + 1 + n * (1 - y[c][p1][p2])
            model += path_increment[c][p1] <= pulp.lpSum(y[c][p1][p2] for p2 in packages) * (n + 1)
        model += pulp.lpSum(y[c][n][p] for p in packages) == 1
        model += pulp.lpSum(y[c][p][n] for p in packages) == 1

    solver = pulp.getSolver(solver, timeLimit=timeout, msg=1)
    model.solve(solver)

    solution = [[n + 1 for _ in range(n + 2)] for _ in couriers]
    for c in couriers:
        for p in packages:
            try:
                if (z_value := int(path_increment[c][p].value())) != 0:
                    solution[c][z_value] = p + 1
            except:
                pass

    return solution, d_max.value() or 0

def minimizer_binary(instance, solver=solve_multiple_couriers, timeout=300):
    return solver(**instance, timeout=timeout)


file_name = r"/Users/aaronsalazar/LocalDocs/Bologna/CDMO/Instances/inst07.dat"

with open(file_name, 'r') as file:
    lines = file.readlines()

m, n = int(lines[0].strip()), int(lines[1].strip())
l, s = [int(x) for x in lines[2].strip().split()], [int(x) for x in lines[3].strip().split()]
D = [list(map(int, line.strip().split())) for line in lines[4:]]

instance = {
    'm': m,
    'n': n,
    'l': l,
    's': s,
    'D': D
}

try:
    solution, min_distance = minimizer_binary(instance)
    print(f"Solution: {solution}")
    print(f"Minimum distance: {min_distance}")
except Exception as e:
    print(f"An error occurred: {e}")