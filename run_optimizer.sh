#! /bin/sh
cd $1
export SCIPOPTDIR=/home/mass/Documents/scipoptsuite-5.0.1/local/usr/local
export PATH=/home/mass/Documents/julia-1.1.0/:$PATH
export JULIA_NUM_THREADS=8
julia -p8 LPCreator.jl && julia -p8 optimizer.jl
