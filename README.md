# CDMO
CDMO Port

# docker
BUIILD = docker build -t cdmo . 
RUN = docker run -it --name cdmo cdmo /bin/bash

The docker run command presented here runs the container and opens a bash terminal to execute comands on.

To execute the commands for CP the following format is expected:
- python3 cp1/try.py <model> <solver> <instance#>

For model you have the following options:

- domwdeg_indrandom
- domwdeg_indrandom_sb
- domwdeg_firstfail
- domwdeg_firstfail_s

For solver you have the following options:

- gecode
- chuffed

For instance please use the correct values from 01-21.

If you would like to run all possible outcomes please use

- python3 cp1/try.py all all all

To execute the commands for SMT the following format is expected:
- python3 smt_final/main.py --model <model> --instance <instance#> --symmetry --runall

For model you have the following options:
- 2d
- 3d

For instance please use the correct values from 01-21.

--symmetry flag is optional to be used to run the models:
- 2d_symmetry
- 3d_symmetry

runall flag is used to run all options of all models that are specified:
Example:
- python3 smt_final/main.py --model 2d --symmetry --runall

To execute the commands for MIP the following format is expected:
- python3 smt_final/main.py --model <model> --instance <instance#> --symmetry --runall

For model you have the following options:
- 2d
- 3d

For instance please use the correct values from 01-21.

--symmetry flag is optional to be used to run the models:
- 2d_symmetry
- 3d_symmetry

--runall flag is used to run all options of all models that are specified:
Example:
- python3 smt_final/main.py --model 2d --symmetry --runall