import json
import os
import minizinc
import traceback
import datetime
import sys
import re
import math

# Define available solvers and models
SOLVERS = ["gecode", "chuffed"]
MODELS = {
    "firstfail_indmin": "cp1/model/firstfail_indmin.mzn",
    "firstfail_indmin_sb": "cp1/model/firstfail_indmin_sb.mzn",
    "domwdeg_indrandom_sb": "cp1/model/domwdeg_indrandom_sb.mzn",
    "domwdeg_indrandom": "cp1/model/domwdeg_indrandom.mzn"
}
RESULT_DIR = "res/CP/"
INSTANCE_DIR = "converted_instances/"

def get_num_load(dzn_file):
    """Extract num_load from the .dzn file."""
    try:
        with open(dzn_file, "r") as f:
            content = f.read()
        match = re.search(r"num_load\s*=\s*(\d+);", content)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return None  # Return None if not found

def solve_minizinc(solver_name, model_path, instance_number):
    try:
        dzn_file = f"{INSTANCE_DIR}inst{instance_number}.dzn"

        if not os.path.exists(dzn_file):
            return {
                "time": 0,
                "optimal": False,
                "obj": None,
                "sol": [],
                "error": f"ERROR: {dzn_file} file not found!"
            }

        num_load = get_num_load(dzn_file)
        if num_load is None:
            return {
                "time": 0,
                "optimal": False,
                "obj": None,
                "sol": [],
                "error": f"ERROR: Could not determine num_load from {dzn_file}!"
            }
        depot_point = num_load + 1  # Set depot dynamically

        # Load MiniZinc model
        model = minizinc.Model()
        model.add_file(model_path)
        solver = minizinc.Solver.lookup(solver_name)

        instance = minizinc.Instance(solver, model)
        instance.add_file(dzn_file)

        # Set timeout
        timeout = datetime.timedelta(seconds=300)

        # Solve the model
        result = instance.solve(timeout=timeout, processes=1)

        # Extract solve time
        solve_time = result.statistics.get("solveTime", 0)
        solve_time = solve_time / 1000.0 if isinstance(solve_time, int) else solve_time.total_seconds()
        solve_time = math.floor(solve_time)

        # Extract and clean solution
        solution_data = []
        if result.solution is not None and hasattr(result.solution, "load_assigned"):
            solution_data = [
                [x for x in group if x != depot_point]  
                for group in result.solution.load_assigned
            ]

        return {
            "time": solve_time,
            "optimal": result.status == minizinc.result.Status.OPTIMAL_SOLUTION,
            "obj": result.objective if hasattr(result, "objective") else None,
            "sol": solution_data
        }

    except minizinc.error.MiniZincError as e:
        return {
            "time": 0,
            "optimal": False,
            "obj": None,
            "sol": [],
            "error": f"MiniZinc error: {str(e)}"
        }
    except Exception as e:
        return {
            "time": 0,
            "optimal": False,
            "obj": None,
            "sol": [],
            "error": f"General error: {traceback.format_exc()}"
        }

def process_instance(solver_name, model_name, instance_number):
    result = {}

    # Handle "all models and solvers" case
    if solver_name == "all" and model_name == "all":
        # For GeCode, use the specific models
        for solver in SOLVERS:
            if solver == "gecode":
                models_to_run = [
                    "domwdeg_indrandom", 
                    "firstfail_indmin_sb", 
                    "domwdeg_indrandom_sb"
                ]
            elif solver == "chuffed":
                # For Chuffed, only use firstfail_indmin_sb model
                models_to_run = ["firstfail_indmin_sb"]
            else:
                models_to_run = []

            for model in models_to_run:
                model_path = MODELS.get(model)
                if model_path:
                    key = f"{solver}_{model}"
                    result[key] = solve_minizinc(solver, model_path, instance_number)


    elif solver_name == "all":
        # Handle case where solver is "all" but specific model is provided
        for solver in SOLVERS:
            if solver == "gecode":
                models_to_run = [
                    "domwdeg_indrandom", 
                    "firstfail_indmin_sb", 
                    "domwdeg_indrandom_sb"
                ]
            elif solver == "chuffed":
                models_to_run = ["firstfail_indmin_sb"]
            else:
                models_to_run = []

            for model in models_to_run:
                model_path = MODELS.get(model)
                if model_path:
                    key = f"{solver}_{model_name}"
                    result[key] = solve_minizinc(solver, model_path, instance_number)

    elif model_name == "all":
        # Handle case where model is "all" but specific solver is provided
        for model, model_path in MODELS.items():
            if solver_name == "chuffed" and model not in ["firstfail_indmin_sb", "firstfail_indmin"]:
                continue

            key = f"{solver_name}_{model}"
            result[key] = solve_minizinc(solver_name, model_path, instance_number)

    else:
        # Handle the case for specific solver and model
        result = solve_minizinc(solver_name, MODELS[model_name], instance_number)

    # Save result as JSON
    os.makedirs(RESULT_DIR, exist_ok=True)
    output_file = os.path.join(RESULT_DIR, f"{int(instance_number)}.json")

    with open(output_file, "w") as f:
        json.dump(result, f, indent=3)

    print(f"Processed instance {instance_number}, result saved to {output_file}")
    print(json.dumps(result, indent=3))


def process_all_instances(solver_name, model_name):
    """Run all available instances in the converted_instances directory."""
    if not os.path.exists(INSTANCE_DIR):
        print(f"Error: Instance directory '{INSTANCE_DIR}' not found.")
        return

    # Get all instance files
    instance_files = sorted(
        [f for f in os.listdir(INSTANCE_DIR) if f.startswith("inst") and f.endswith(".dzn")]
    )

    if not instance_files:
        print("Error: No instances found in the converted_instances directory.")
        return

    for instance_file in instance_files:
        instance_number = re.search(r"inst(\d+)\.dzn", instance_file).group(1)
        process_instance(solver_name, model_name, instance_number)

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python try.py [solver] [model] [instance_number/all]")
        print("Example: python try.py gecode firstfail_indmin 01")
        print("Use 'all' for solver and/or model to run all available options.")
        print("Use 'all' as instance_number to run all instances.")
        sys.exit(1)

    solver_arg = sys.argv[1].lower()
    model_arg = sys.argv[2].lower()
    instance_arg = sys.argv[3].lower()

    if solver_arg != "all" and solver_arg not in SOLVERS:
        print(f"Error: Invalid solver '{solver_arg}'. Choose from {SOLVERS} or 'all'.")
        sys.exit(1)

    if model_arg != "all" and model_arg not in MODELS:
        print(f"Error: Invalid model '{model_arg}'. Choose from {list(MODELS.keys())} or 'all'.")
        sys.exit(1)

    if instance_arg == "all":
        process_all_instances(solver_arg, model_arg)
    else:
        if not instance_arg.isdigit() or int(instance_arg) < 1:
            print("Error: Instance number must be a positive integer.")
            sys.exit(1)

        instance_number = f"{int(instance_arg):02d}"
        process_instance(solver_arg, model_arg, instance_number)
