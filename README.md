[![License: GPL v3](https://img.shields.io/badge/License-GPL%20v3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
![Python3.6](https://img.shields.io/badge/Language-Python_3.6-steelblue.svg)
![Bash](https://img.shields.io/badge/Language-Bash-green.svg)
[![Twitter URL](https://img.shields.io/twitter/url/https/twitter.com/klamkiewicz?label=%40klamkiewicz&style=social)](https://twitter.com/klamkiewicz)

# Thogotovirus Host adaptation experiments
## Supplement scripts for Fuchs et al. (2020), "TITLE", "Journal", doi: 


In order to use our scripts, transform the .vcf files created by [LoFreq](https://csb5.github.io/lofreq/) with the following `bash/awk` loop.

```bash
for file in "$WORKDIR"/assembly_mapping/*vcf; do
  awk -v OFS='\t' '/^[^#]/ {split($NF,info,";"); split(info[1], cov, "="); split(info[2], freq, "="); print $1, $2, $4, $5, cov[2], freq[2]}' $file > ${file%.*}_snp_summary.csv
done
```

That way, the SNPs are already in a somewhat readable format.


### Circos information files

If you'd like to create the files for the circos plots based on the SNP-calling, we refer to `parse_circos.py`:

```
python3 parse_circos.py <SNP-FILE> <REFERENCE> <MAPPING-FILE> <OUTPUT_DIRECTORY>
```
Here, the `SNP-FILE` corresponds to the one created with the bash/awk command above. The `REFERENCE` simply contains 
the reference genome in FASTA format. The `MAPPING-FILE` can be a `.sam`, `.bam` or `.cram` file, produced by nearly all
mapping tools. Last, the `OUTPUT_DIRECTORY` specifies the folder where the configurations files are stored.

### Determine changes in the protein sequence

The script `create_mutated_seqs.py` reads in all information coming from the SNP-file and the reference. 
With that, for each SNP a new FASTA file is created which contains this particular SNP. Next, the [EMBOSS getorf](http://emboss.sourceforge.net/apps/cvs/emboss/apps/getorf.html)
script is invoked to determine the protein sequences. In our case, looking for the largest ORF predicted on
a segment resulted in the actual protein in all cases. 
Our script takes this new information and updates the `*snp_summary.csv` table with the information, whether a SNP
leads to a synonymous, silencing or non-synonymous change in protein level.

```
python3 create_mutated_seqs.py <REFERENCE> <SNP-FILE> <OUTPUT_DIRECTORY>
```

The parameters are the same as described above.