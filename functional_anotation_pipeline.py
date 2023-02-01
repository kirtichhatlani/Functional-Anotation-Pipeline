#!/usr/bin/env python 

import subprocess
import shlex
import argparse
import os
# os.system()
parser = argparse.ArgumentParser(description="Runs the full Functional Annotation Pipeline. This includes clustering followed by phobius, deeparg, blasting vfdb, and signalp. The gff's are merged and returned in the output folder in output.gff3. The cluster_info subfolder contains the clusters and fused .fasta and .faa files.")
parser.add_argument('-p', '--prokka', required=True,
                    help='Path of the directory with .faa and .gff prokka output files are')
parser.add_argument('-dm', '--deepargmodel', required=False, default='/home/groupc/bin/deeparg_downloads/',
                    help='Path of the directory where the deeparg model is stored')
parser.add_argument('-de', '--deepargenv', required=False, default='team3_functional_annotation',
                    help='Path of the conda environment where deeparg is installed')
parser.add_argument('-dx', '--deepargexecutable', required=False, default='/home/groupc/bin/anaconda_reinstall/envs/deeparg_conda2/bin/deeparg',
                    help='Path of the directory where the deeparg executable is stored')
parser.add_argument('-sp', '--signalpenv', required=False, default='team3_signalp6',
                    help='Conda environment signalp6 is installed in')
parser.add_argument('-bp', '--blastpenv', required=False, default='team3_functional_annotation',
                    help='Conda environment blastp is installed in')
parser.add_argument('-bpdb', '--blastpdb', required=False, default='/home/groupc/files/functional_annotation/VFDB/VFDB_setB_pro.fas',
                    help='Path of the blastp database')
parser.add_argument('-ph', '--phobius', required=False, default='/home/groupc/tmp/tmpckJtGA/phobius/phobius.pl',
                    help='Path of the phobius .pl file')
args = parser.parse_args()
working_dir = 'functional_annotation_temporary_working_directory'

os.system(f'rm -r {working_dir}')
os.system(f'mkdir {working_dir}')
os.system(f'mkdir {working_dir}/cluster_info')
os.system(f'mkdir {working_dir}/tmp')

print('RUNNING usearch')
os.system(f'cat {args.prokka}*/*.faa > ./{working_dir}/cluster_info/combined_prokka.faa')
os.system(f'./bin/usearch -cluster_fast ./{working_dir}/cluster_info/combined_prokka.faa -id 0.97 -centroids {working_dir}/cluster_info/nr_097.faa -uc {working_dir}/cluster_info/nr_097.faa.uc -sort length')

print('RUNNING blastp on VFDB')
here = os.getcwd()
os.system(f'eval "$(conda shell.bash hook)"; conda activate {args.blastpenv}; blastp -db {args.blastpdb} -query {here}/{working_dir}/cluster_info/nr_097.faa -out {here}/{working_dir}/tmp/VFDB.out -max_target_seqs 1 -max_hsps 1 -outfmt "6 qseqid qstart qend sseqid evalue sstart send sframe stitle" -evalue 1e-10')
os.system(f'./bin/VFDB2gff.py {working_dir}/tmp/VFDB.out {working_dir}/tmp/VFDB.gff')

print('RUNNING phobius')
os.system(f'{args.phobius} -short {working_dir}/cluster_info/nr_097.faa > {working_dir}/tmp/phobius.txt')
os.system(f'./bin/phobius2gff.py -i {working_dir}/tmp/phobius.txt -f {working_dir}/cluster_info/nr_097.faa')

print('RUNNING deeparg')
os.system(f'eval "$(conda shell.bash hook)"; conda activate {args.deepargenv}; {args.deepargexecutable} predict --model SS --type prot -i "{working_dir}/cluster_info/nr_097.faa" -o "{working_dir}/tmp/deeparg.out" -d {args.deepargmodel}')
os.system(f'./bin/deeparg2gff.py -i {working_dir}/tmp/deeparg.out.mapping.ARG')

print('RUNNING signalp6')
os.system(f'eval "$(conda shell.bash hook)"; conda activate {args.signalpenv}; signalp6 -ff {working_dir}/cluster_info/nr_097.faa -fmt none -od {working_dir}/tmp/signalp')

print("MERGING gff's")
os.system(f'./bin/merge_gff.py -d {working_dir}/tmp/deeparg.out.mapping.ARG.gff3 -p {working_dir}/tmp/phobius.gff3 -v {working_dir}/tmp/VFDB.gff -s {working_dir}/tmp/signalp/region_output.gff3 -c {working_dir}/cluster_info/nr_097.faa -o {working_dir}/output.gff3')

print("REMERGING with prokka")
os.system(f"ls {args.prokka}*/*.gff | xargs ./bin/reverse_uclust.py -g {working_dir}/output.gff3 -c {working_dir}/cluster_info/nr_097.faa.uc -p")

print("DELETING working directory")
os.system(f'rm -r {working_dir}')
