#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Author: Kevin Lamkiewicz
# E-Mail: kevin.lamkiewicz@uni-jena.de

"""
This script is part of the publication
"TODO -- Insert Title here"
by Jonas Fuchs et al. 2020

SNP information generated by lofreq are taken and parsed into configuration files for 
circos plotting.

"""

##################
# import section #
##################

import sys
import subprocess
import csv
import os
from glob import glob

#######################
# auxiliary functions #
#######################

def read_sequence(fastaFile, rna=True):
    """
    Read the sequences in .fasta format.
    -----------------------------------------------------
    Keyword arguments:
    fastaFile -- Path to the sequence file.
    rna -- Flag whether RNA sequences are read. If 'True' the 'U' nucleotides are replaced with 'T'
    """

    sequences = {}
    with open(fastaFile, 'r') as inputStream:
      header = ''
      seq = ''

      for line in inputStream:
        if line.startswith(">"):
          if header:
            sequences[header] = seq
          header = line.rstrip("\n").replace(':','_').replace(' ','_').lstrip(">")
          seq = ''
        else:
          seq += line.rstrip("\n").upper()#.replace('U','T')
          if rna:
            seq = seq.replace('U','T')
      sequences[header] = seq
    return sequences


def read_snp_file(snpFile):
  """
  Uses the csv module to read in the SNP summary file. 
  All values are parsed and the relative amount of SNPs per position 
  are transformed with the math.log10() function.

  Note: as lofreq doesn't report SNPs with coverage '0', the log function
  won't fail in this particular case.
  -----------------------------------------------------------------------
  Keyword arguments:
  snpFile -- path to the .csv file containing the SNP information
  """
  
  with open(snpFile, 'r') as inputStream:
      reader = csv.reader(inputStream, delimiter="\t")
      for row in reader:
        segment = row[0]
        position = int(row[1])
        snp = row[3]
        coverage = int(row[4])
        snpFreq = float(row[5])*100
        if segment in snps:
          snps[segment][position] = snp
          frequencies[segment][position] = (coverage, snpFreq)
        else:
          snps[segment] = {position : snp}
          frequencies[segment] = {position : (coverage, snpFreq)}

def find_mutation(ref, mut):
  """
  A very simple method to find the differences between
  two aminoacid sequences. If none are found, the
  mutation between the two viruses is a synonymous mutation.
  -----------------------------------------------------------------------
  Keyword arguments:
  ref -- Aminoacid sequence derived from the wildtype virus
  mut -- Aminoacid sequence derived from the mutated virus
  """

  for idx, refAA in enumerate(ref):
    if refAA != mut[idx]:
      return(f"{refAA}->{mut[idx]}")
  return("Synonymous")


###############
# MAIN METHOD #
###############

if __name__ == "__main__":
  # global variable definitions
  referenceFile = sys.argv[1]
  csvSNPs = sys.argv[2]
  outputDir = sys.argv[3]
  outputDir = f"{outputDir}/{os.path.basename(csvSNPs).split('.')[0]}"
  
  if not os.path.isdir(outputDir):
    os.mkdir(outputDir)
  
  chromosomes = {}
  snps = {}
  frequencies = {}

  chromosomes = read_sequence(referenceFile)
  read_snp_file(csvSNPs)

  # create fasta files with all segment variations  
  for segment, snpPos in snps.items():
    refSegment = chromosomes[segment]
    with open(f"{outputDir}/{segment}.fasta",'w') as outputStream:
      outputStream.write(f">{segment}\n{refSegment}\n")
    for pos, snp in snpPos.items():
      mutatedSegment = refSegment[:pos] + snp + refSegment[pos+1:]
      with open(f"{outputDir}/{segment}_{pos}.fasta",'w') as outputStream:
        outputStream.write(f">{segment}\n{mutatedSegment}\n")

  # for each variation, extract the ORF using EMBOSS getorf
  for file in glob(f"{outputDir}/*fasta"):
    outfile = os.path.splitext(file)[0]
    cmd = f"getorf -sequence {file} -outseq {outfile}.orf"
    subprocess.run(cmd.split(), stderr=subprocess.DEVNULL)
  
  wildtypeORFs = {}
  mutatedORFs = {}

  # extract the longest ORF for each sequence
  # in our case, this is the protein coding ORF
  # described in literature
  for file in glob(f"{outputDir}/*orf"):
    orfs = read_sequence(file, rna=False)
    longestORF =  sorted(orfs, key=lambda k: len(orfs[k]), reverse=True)[0]
    file = os.path.splitext(os.path.basename(file))[0]
    orfRange = longestORF.split('[')[1].replace('_','').rstrip(']').split('-')

    # make sure to seperate WT and Mutation ORFs
    if any([file.endswith(f"Segment_{i}") for i in range(1,7)]):
      wildtypeORFs[file] = (orfRange, orfs[longestORF])  
    else:
      mutatedORFs[file] = (orfRange, orfs[longestORF])
  
  print("Segment\tPosition\tWT\tSNP\tCoverage\t%SNP\tMutation_Type")
  for segment, snpPos in snps.items():
    refRange, referenceORF = wildtypeORFs[segment]
    for pos, snp in snpPos.items():
      mutRange, mutatedORF = mutatedORFs[f"{segment}_{pos}"]
      # if the ranges of the ORFs do not match,
      # a stop codon has been introduced by the mutation
      if refRange[0] != mutRange[0] or refRange[1] != mutRange[1]:
        mutation = "Silencing"
      else:
        mutation = find_mutation(referenceORF, mutatedORF)
      print(f"{segment}\t{pos}\t{chromosomes[segment][pos-1]}\t{snp}\t{frequencies[segment][pos][0]}\t{frequencies[segment][pos][1]:.2f}\t{mutation}")
      
