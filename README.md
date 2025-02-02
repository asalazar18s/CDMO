# CDMO
CDMO Port

# docker
BUIILD = docker build -t cdmo . 
RUN = docker run -it --name cdmo cdmo /bin/bash

The docker run command presented here runs the container and opens a bash terminal to execute comands on.

To execute the commands for CP the following format is expected:
- python3 cp1/try.py <model> <solver> <instance#>
For model you have the following options:

For solver you have the following options:

For instance please use the correct values from 01-21.

