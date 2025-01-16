include "globals.mzn";

% Define parameters
int: num_couriers;
int: num_load;
array[1..num_couriers] of int: courier_capacity;
array[1..num_load] of int: load_size;
array[1..num_load+1, 1..num_load+1] of int: distance;

% Decision variables
array[1..num_couriers, 1..num_load+2] of var 1..num_load+1: load_assigned;

% Total distance traveled by each courier
array[1..num_couriers] of var int: total_distance = 
    [sum(load in 1..num_load)(distance[load_assigned[courier, load], load_assigned[courier, load+1]]) | courier in 1..num_couriers];

% Total weight carried by each courier 
array[1..num_couriers] of var int: weights = 
    [sum(load in 2..num_load+1 where load_assigned[courier, load] != num_load+1)(load_size[load_assigned[courier, load]]) | courier in 1..num_couriers];

% Objective: minimize the maximum distance travelled
var int: z = max(total_distance);

% Constraints

% Each load must go to one courier and be picked up only once
constraint
    all_different([load_assigned[courier, load] | courier in 1..num_couriers, load in 2..num_load+1 where load_assigned[courier, load] != num_load+1]);

% Each load must be assigned to some courier
constraint
    forall(load in 1..num_load)(
        exists(courier in 1..num_couriers, pos in 2..num_load+1)(load == load_assigned[courier, pos])
    );

% Each courier's total load must be within their capacity limit
constraint
    forall(courier in 1..num_couriers)(weights[courier] <= courier_capacity[courier]);

% Each courier must begin and end at the base
constraint
    forall(courier in 1..num_couriers)(
        load_assigned[courier, 1] = num_load+1 /\ load_assigned[courier, num_load+2] = num_load+1
    );

% Each courier must pick up a load immediately after leaving the base
constraint
    forall(courier in 1..num_couriers)(
        exists(pos in 2..num_load+1)(load_assigned[courier, pos] != num_load+1) -> load_assigned[courier, 2] != num_load+1
    );

% Ensure each courier has at least one load assigned
constraint
    forall(courier in 1..num_couriers)(
        exists(load in 2..num_load+1)(load_assigned[courier, load] != num_load+1)
    );

solve :: int_search([load_assigned[courier, pos] | courier in 1..num_couriers, pos in 2..num_load+1], dom_w_deg, indomain_random) minimize z;

% Output: Route for each courier and the corresponding total distance
output [
  "Courier " ++ show(i) ++ ": " ++ show([load_assigned[i,j] | j in 2..num_load+1 where load_assigned[i,j] != num_load+1]) ++ 
  ", Distance: " ++ show(total_distance[i]) ++ "\n" 
  | i in 1..num_couriers
];
