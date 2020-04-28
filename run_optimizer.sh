#! /bin/sh
cd ../MASS-Optimizer/optimizer/
# ./HOM_LPCreator ./Input_File.txt
julia -p8 LPCreator.jl
julia -p8 optimizer.jl
