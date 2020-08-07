#! /bin/sh
cd $1
# ./HOM_LPCreator ./Input_File.txt
julia -p8 LPCreator.jl
julia -p8 optimizer.jl
