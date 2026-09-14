# Match Reactome metabolic genes with expression matrix genes
import os
import pandas as pd

# Ensure we're in the right directory
os.chdir('C:/Users/User/Desktop/agentic/3CA/Q1_R14')

# Read Reactome metabolic genes
reactome_genes = set()
with open('sources/reactome/metabolism_R-HSA-1430728_release_97_genes.txt', 'r') as f:
    for line in f:
        gene = line.strip()
        if gene:
            reactome_genes.add(gene)

# Read expression matrix genes
expression_genes = set()
with open('inputs/Genes.txt', 'r') as f:
    for line in f:
        gene = line.strip()
        if gene:
            expression_genes.add(gene)

# Find matched genes (intersection)
matched_genes = reactome_genes.intersection(expression_genes)

# Count
print(f"Reactome metabolic genes: {len(reactome_genes)}")
print(f"Expression matrix genes: {len(expression_genes)}")
print(f"Matched metabolic genes: {len(matched_genes)}")

# Save matched genes list
with open('results/matched_metabolic_genes.txt', 'w') as f:
    for gene in sorted(matched_genes):
        f.write(gene + '\n')

# Save mapping of duplicate symbols in expression matrix
# First, count symbol occurrences
from collections import Counter
symbol_counts = Counter()
with open('inputs/Genes.txt', 'r') as f:
    for line in f:
        gene = line.strip()
        if gene:
            symbol_counts[gene] += 1

# Find duplicate symbols
duplicates = {sym: count for sym, count in symbol_counts.items() if count > 1}
print(f"\nDuplicate symbols in expression matrix: {len(duplicates)}")
for sym, count in sorted(duplicates.items(), key=lambda x: -x[1])[:10]:
    print(f"  {sym}: {count} rows")

# Save source-to-symbol mapping
with open('results/source_feature_to_symbol.csv', 'w') as f:
    f.write("source_gene,symbol\n")
    for i, gene in enumerate(expression_genes):
        f.write(f"{i},{gene}\n")

print("\nDone!")
