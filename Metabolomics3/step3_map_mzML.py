import pandas as pd
from os import path

def find_mzml_file(filename, base_dir):
    """
    This function searches for the mzML file in a directory corresponding to a given filename.

    Parameters:
        filename (str): The name of the .raw-file which the sought .mzML-file corresponds to.
        base_dir (str): Path to the directory where the .mzML files are located.

    Returns:
        str: The path to the found .mzML file or an error message if it could not be discovered.
    """
    # Generate mzML filename from raw filename
    mzml_filename = f"{filename}.mzML"

    # Check if the file exists in base directory
    fullpath = path.join(base_dir, mzml_filename)

    if path.isfile(fullpath):
        return fullpath
    else:
        raise Exception(fullpath + ' not found')

def main():
    """
    The main function of the script which drives the entire program flow.
    """
    # Inputs and definitions
    csv_file = 'combined_sequences.csv'  # CSV file containing the filenames for search
    mzml_dir = '../ALL_MZML/'  # Directory where to find the .mzML files
    output_csv = 'pcpfm_sequence.csv'  # Output CSV file with matched filename and mzML paths

    # Load data from CSV into a DataFrame
    df = pd.read_csv(csv_file)

    # Find the matching .mzML for each .raw-filename in the DataFrame
    df['mzml_path'] = [find_mzml_file(name, mzml_dir) for name in df['File Name']]

    # Write DataFrame with added column to a new CSV file
    df.to_csv(output_csv, index=False)

# This call statement ensures the main function only runs if the script is executed directly (not imported as module)
if __name__ == '__main__':
    main()