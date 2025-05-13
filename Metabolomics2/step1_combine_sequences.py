"""
Documentation: This script combines multiple CSV sequence files into one single CSV file, named "combined.csv".
The script ignores the first row of each CSV file (assuming headers are present) and appends all data to a Pandas DataFrame object.
After reading all applicable files, it writes this aggregated DataFrame to the output CSV file at the specified location.
This facilitates easier handling and analysis of sequential data from multiple inputs.
"""

import pandas as pd
import os


def add_metadata(df):
   """Updates the 'Sample Type' column."""
   df.loc[df['OriginSequence'].str.contains('supernatant'), "Harvest"] = "Supernatant"
   df.loc[df['OriginSequence'].str.contains('pellet'), "Harvest"] = "Pellet"
   return df

def combine_sequences(directory):
   """Combines all sequence files found in given directory into one."""
   dfs = []
   file_count = 0
   method_counts = {}

   for file in os.listdir(directory):
       if file.endswith(".csv"):
           file_count += 1
           df = pd.read_csv(os.path.join(directory, file), skiprows=1)
           df['OriginSequence'] = file.lower()
           df['Method'] = df['Instrument Method']
           df = add_metadata(df)
           dfs.append(df)
           # Count unique 'Method's in this CSV file
           methods = df['Instrument Method'].unique()
           for method in methods:
               if method in method_counts:
                   method_counts[method] += 1
               else:
                   method_counts[method] = 1

   combined = pd.concat(dfs, ignore_index=True)
   output_file = "combined_sequences.csv"
   combined.to_csv(output_file, index=False)

   return file_count, method_counts

def main():
   import json
   """Main function calling the sequence file combination."""
   directory = "./sequences" # path to directory containing CSV sequence files
   file_count, method_counts = combine_sequences(directory)
   print("Combination successful.")
   print("File count:", file_count)
   print("Method counts:\n", json.dumps(method_counts, indent=4))

if __name__ == '__main__':
   main()
