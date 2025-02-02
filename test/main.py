
import argparse
import sys
from utils import *
from solver_model import solve_multiple_couriers 
def main():
    # Initialize the argument parser
    parser = argparse.ArgumentParser(description="Courier Assignment Problem Solver using Z3.")
    
    # Define command-line arguments
    parser.add_argument(
        "--solver", 
        type=str, 
        required=True, 
        choices=["PULP_CBC_CMD", "1", ""], 
        help="Specify the model to use: 'MIP'"
    )
    parser.add_argument(
        "--instance", 
        type=str,
        help="Specify the instance number (e.g., '07' for 'inst07.dat')."
    )
    parser.add_argument(
        "--runall",
        action="store_true",
        help="Enable running all instances."
    )
    
    # Parse the arguments
    args = parser.parse_args()
    
    if args.runall:
        print("runall")
        for i in range(1,23):
            if i < 10:
                # Construct the instance file path
                instance_filename = f"inst0{i}.dat"
                
            else: 
                instance_filename = f"inst{i}.dat"
            
            # Read the data file
            instance_filepath = f"Instances/{instance_filename}"

            try:
                m, n, l, sizes, D_matrix = read_dat_file(instance_filepath)
            except FileNotFoundError:
                print(f"Error: Instance file '{instance_filepath}' not found.")
                sys.exit(1)
            except Exception as e:
                print(f"Error reading instance file: {e}")
                sys.exit(1)


            # Select and run the specified model
            
            solve_multiple_couriers(m, n, D_matrix, l, sizes, args.solver)
            print(f"------------------------------INSTANCE {instance_filename} RUNNING-------------------------------------")
    else:
        # Read the data file
        instance_filename = f"inst{args.instance}.dat"
        instance_filepath = f"Instances/{instance_filename}"
        try:
            m, n, l, sizes, D_matrix = read_dat_file(instance_filepath)
        except FileNotFoundError:
            print(f"Error: Instance file '{instance_filepath}' not found.")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading instance file: {e}")
            sys.exit(1)

        solve_multiple_couriers(m, n, D_matrix, l, sizes, args.solver)

if __name__ == "__main__":
    main()
