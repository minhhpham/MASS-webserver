#! /bin/sh
../MASS-Optimizer/optimizer/HOM_LPCreator Input_File.txt
julia -p8 optimizer.jl