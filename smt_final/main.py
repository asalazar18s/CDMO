# main.py

import argparse
import sys
from smt1 import run_model_2d
from smt3 import run_model_3d
# from smt2 import run_model_2d
from utils import read_dat_file

def main():
    # Initialize the argument parser
    parser = argparse.ArgumentParser(description="Courier Assignment Problem Solver using Z3.")
    
    # Define command-line arguments
    parser.add_argument(
        "--model", 
        type=str, 
        required=True, 
        choices=["2d", "3d"], 
        help="Specify the model to use: '2d' or '3d'."
    )
    parser.add_argument(
        "--instance", 
        type=str,
        help="Specify the instance number (e.g., '07' for 'inst07.dat')."
    )
    parser.add_argument(
        "--symmetry",
        action="store_true",
        help="Enable symmetry breaking constraints."
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
            
            origin = n  # Assuming origin is indexed at n
            ITEMS = list(range(n))  # Adjust if ITEMS is a subset


            # Select and run the specified model
            if args.model.lower() == "2d":
                run_model_2d(m, n, l, sizes, D_matrix, origin, args.symmetry, i)
            elif args.model.lower() == "3d":
                run_model_3d(m, n, l, sizes, D_matrix, origin, args.symmetry, args.instance)
            else:
                print(f"Error: Unknown model '{args.model}'. Choose '2d' or '3d'.")
                sys.exit(1)

            print(f"------------------------------INSTANCE {instance_filename} DONE-------------------------------------\n\n")
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
        
        origin = n  # Assuming origin is indexed at n
        
        # Select and run the specified model
        if args.model.lower() == "2d":
            run_model_2d(m, n, l, sizes, D_matrix, origin, args.symmetry, args.instance)
        elif args.model.lower() == "3d":
            run_model_3d(m, n, l, sizes, D_matrix, origin, args.symmetry, args.instance)
        else:
            print(f"Error: Unknown model '{args.model}'. Choose '2d' or '3d'.")
            sys.exit(1)

if __name__ == "__main__":
    main()
