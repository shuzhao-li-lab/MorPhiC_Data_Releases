# MorPhiC Data Release

This repository contains all processing for the morphic data release on 05_15_2025. It implements a metabolomics preprocessing pipeline using the **PCPFM** (Python-Centric Pipeline For Metabolomics) for high-resolution data analysis. The pipeline was developed by Joshua Mitchell, Yuanye Chi, Shuzhoe Li and others at the (Jackson Laboratory) for processing iPSC (induced pluripotent stem cell) metabolomics data, but it can be applied to other LC-MS datasets. **PCPFM** provides an end-to-end solution built on Asari for feature detection, quality control, and annotation. The pipeline accepts raw Thermo `.RAW` files (after conversion to mzML) or directly `.mzML` files, along with sample metadata, and produces human-readable tables of detected metabolomic features with annotations and associated sample information.

This repository is largely for handing off Morphic to the DRACC directly, a previous analysis of the data can be found here: PR001844. Note, that re-analysis of the dataset can yield new results as the uploaded feature tables pre-date the analysis and this version of the software. 

## Features

* **Comprehensive Workflow:** Automates raw data conversion (Thermo `.RAW` to `.mzML`), feature extraction using Asari, data curation (normalization, QC), and multi-level metabolite annotation via PCPFM. For this initial version no normalization is performed or other qa/qc as these can be highly variable and tailored to individual analyses. This gives us an annotation table for non-derivatization samples with PCPFM Level4 and Level2 annotations and 

* **High-Performance Peak Picking:** Utilizes Asari for scalable, high-resolution peak detection (leveraging high mass accuracy for better alignment).

* **Structured Outputs:** The pipeline outputs are organized by experiment and processing mode. For each subset of samples (e.g. by chromatography mode and sample type), PCPFM creates an experiment folder containing subdirectories for raw converted files, Asari results (feature tables), annotations, and final result tables. This makes downstream analysis straightforward (e.g., in R or MetaboAnalyst).

* **Extensibility:** The pipeline supports additional steps like MS/MS spectral mapping and custom database annotations. It can generate PDF reports and apply normalization or batch corrections as needed. These are in the files for future use or exploration but commented out for reasons described above. 

## Setup and Installation

### Using Docker (Recommended)

A Docker image is provided to encapsulate all dependencies. The Dockerfile uses Ubuntu as base and installs Python 3, Asari, PCPFM, and conversion tools. Key components installed in the image:

* **Python 3.11** (for running pipeline scripts and PCPFM).
* **Asari** and **PCPFM** (installed via `pip` for the latest versions).
* **Thermo RawFileParser** (and Mono) for converting Thermo `.RAW` files to `.mzML` within the container. The converter (`ThermoRawFileParser.exe`) is placed in `/usr/local/thermo/` and can be run with the Mono runtime.

**Building the Docker image:** Ensure you have Docker installed, then build from the project directory (containing the Dockerfile and pipeline scripts) [UNTESTED]:

```bash
docker build -t asari_pcpfm_pipeline .
```

This command will produce an image named `asari_pcpfm_pipeline` with all necessary software.

**Running the container:** To use the pipeline, run the container and mount your data directories as volumes so the pipeline can access input files and save outputs. For example:

```bash
docker run -it \
  -v /path/to/your/sequences:/pipeline/sequences \
  -v /path/to/your/config:/pipeline/config \
  -v /path/to/your/mzML_files:/pipeline/ALL_MZML \
  -v /path/to/your/filters:/pipeline/pcpfm_filters \
  asari_pcpfm_pipeline bash
```

In this example, we assume:

* Your instrument sequence CSV files are in a directory `/path/to/your/sequences` on the host (mounted to `./sequences` in the container).
* Your PCPFM metadata JSON (see **Step 2** below) is in `/path/to/your/config` (mounted to `./config` in the container).
* Your converted mzML files are in `/path/to/your/mzML_files` (mounted to `../ALL_MZML` relative to the pipeline working directory).
* Your PCPFM filter JSON files (for different chromatography modes or sample subsets) are in `/path/to/your/filters` (mounted to `./pcpfm_filters` in the container).

After running the above, you will get an interactive shell inside the container at the pipeline working directory (`/pipeline`). You can then execute the pipeline steps as described in [Running the Pipeline](#running-the-pipeline). All output files will be written to the mounted volumes (e.g., results will appear under the `./results` directory inside the container, which you can map to a host directory if needed).

**Note:** If you are starting from Thermo `.RAW` files, convert them to mzML first. The container includes Thermo RawFileParser for conversion. For example, to convert all RAW files in a directory:

```bash
mono /usr/local/thermo/ThermoRawFileParser.exe -d /pipeline/raw_files -o /pipeline/ALL_MZML -f=1
```

This will convert RAW files from `/pipeline/raw_files` to mzML format in `/pipeline/ALL_MZML` (the `-f=1` flag specifies mzML output). Alternatively, use ProteoWizard’s MSConvert if available. Once mzML files are ready, proceed with the pipeline steps.

### Local Installation (Alternative)

If not using Docker, you will need to install the required tools manually:

* **Python 3.8+** (Python 3.11 recommended for compatibility with the provided scripts).
* **Asari**: `pip install asari-metabolomics`
* **PCPFM**: `pip install pcpfm` (this will also install Asari and other dependencies).
* **Mono** runtime and Thermo RawFileConverter\*\*/Parser\*\* if you need to convert Thermo RAW files (install `mono-devel` or `mono-complete` on Linux, and download `ThermoRawFileParser.exe` from the [CompOmics release page](https://github.com/compomics/ThermoRawFileParser/releases)). Place the `.exe` in a known location and use `mono` to run it as shown above.
* **Pandas** and other Python libraries (these are installed automatically with PCPFM, but ensure you have `pip` and a C compiler for any dependencies that might need compilation).

Ensure that the pipeline scripts (`step1_combine_sequences.py`, etc.) are in your working directory. The following sections assume the pipeline is being run in the prepared Docker environment or an equivalently configured local environment.

## Running the Pipeline

The pipeline consists of four main steps that should be run in sequence. Below is an overview of each step with its purpose and how to execute it. **Before you begin**, make sure you have organized the input files as follows:

* **Sequence CSV files**: one or more CSV files (exported from the instrument sequence or sample list) containing sample run metadata. These will be combined in Step 1. Place them in a directory (default expected path is `./sequences`).
* **PCPFM metadata JSON**: a JSON file defining how to assign or adjust sample metadata (like sample type) based on substrings (used in Step 2). The default expected path is `./config/search_dict.json`.
* **Converted mzML files**: all `.mzML` files corresponding to your samples. Ensure each file name matches the sample file name in the sequence metadata (see Step 3). By default, the script looks in `../ALL_MZML/` relative to the pipeline directory.
* **PCPFM filter files**: JSON files that specify subsets of samples to process together (e.g., grouping by chromatography mode or other criteria). These are used in Step 4 and expected in `./pcpfm_filters/`. Each filter file corresponds to one analysis subgroup.

### Step 1: Combine Sequence Metadata

**Script:** `step1_combine_sequences.py`
**Function:** Combines multiple sequence CSV files into a single consolidated CSV (`combined_sequences.csv`). This step reads all `.csv` files in the specified directory (by default `./sequences`), skips the first header row of each, and appends the contents. It also adds some derived columns:

* **OriginSequence:** The source file name (lowercased) from which each row originated (useful if you have multiple sequence files).
* **Method:** Duplicated from the `Instrument Method` column for convenience.
* **Harvest:** Categorized as `"Supernatant"` or `"Pellet"` based on whether the `OriginSequence` filename contains those substrings (this is a custom classification for sample harvest type).

**Usage:** From the pipeline directory, run:

```bash
python3.11 step1_combine_sequences.py
```

This will look for CSV files in `./sequences` and produce `combined_sequences.csv` in the current directory. After a successful run, it will report how many files were combined and the count of unique instrument methods found.

*Output:* `combined_sequences.csv` – a merged table of all samples with their original metadata. Ensure that this file contains expected columns like **File Name**, **Instrument Method**, **Sample Type**, etc., inherited from your sequence files.

### Step 2: Add PCPFM Metadata

**Script:** `step2_add_pcpfm_metadata.py`
**Function:** Augments the combined metadata with additional annotations as defined in a JSON configuration. Specifically, this script updates the **Sample Type** (or other fields) for each sample based on certain substrings found in specified metadata fields. The JSON config (default path `./config/search_dict.json`) should define a list of rules. Each rule can map a substring (or pattern) to a new Sample Type label. For example, one might use this to label samples as "QC", "Blank", "Standard", etc., based on identifiers in the sample name or another column.

**Usage:** Ensure your JSON config is prepared, then run:

```bash
python3.11 step2_add_pcpfm_metadata.py
```

This script will read `combined_sequences.csv` (from Step 1) and the JSON config file, apply the metadata rules, and overwrite the `combined_sequences.csv` with updated values (the output file path is the same by default). No new file is created for this step (it updates the existing combined CSV in-place with refined sample annotations).

*Output:* An updated `combined_sequences.csv` with enriched metadata. You should see the **Sample Type** column (and possibly others) appropriately filled or adjusted according to your `search_dict.json` rules. This ensures PCPFM has the correct sample type labels for downstream processing (which can affect QC and normalization steps).

### Step 3: Map mzML Files to Samples

**Script:** `step3_map_mzML.py`
**Function:** Links each sample entry in the combined metadata to its corresponding mzML file path. The script reads the `combined_sequences.csv` from previous steps and looks for each sample’s mzML file in a given directory. It uses the **File Name** field from the CSV to construct the expected mzML filename. For instance, if a sample’s File Name is "Sample\_A1" (or "Sample\_A1.raw"), it will look for "Sample\_A1.mzML" in the specified folder of mzML files. If found, the full path is recorded.

By default, the directory for mzML files is set to `../ALL_MZML/` (one level up from the pipeline directory). Make sure your mzML files are placed accordingly or adjust the script’s `mzml_dir` variable. Each sample’s **mzml\_path** will be added to the metadata.

**Usage:** Run the mapping script:

```bash
python3.11 step3_map_mzML.py
```

This will search for each file in `../ALL_MZML/` and update the metadata. If any expected mzML file is missing, the script will raise an error for that file.

*Output:* `pcpfm_sequence.csv` – a new CSV file similar to the combined metadata but with an extra column, `mzml_path`, giving the path to each sample’s mzML file. This file will serve as the input sequence file for the PCPFM pipeline in the next step.

**Note:** Make sure that the **File Name** entries in `combined_sequences.csv` match the mzML filenames. For example, if the File Name includes the `.raw` extension (e.g., "Sample1.raw"), the script will look for "Sample1.raw\.mzML" unless adjusted. In practice, you may want to ensure the File Name in the CSV does *not* include the extension, or modify the script to handle it. By default, the code assumes File Name is a base name (without extension). Verify `pcpfm_sequence.csv` to ensure paths are correct before proceeding.

### Step 4: PCPFM Processing and Feature Extraction

**Script:** `step4_pcpfm_process.sh`
**Function:** Orchestrates the core metabolomics processing using the PCPFM pipeline (which internally uses Asari and other tools). This Bash script will iterate over each filter JSON in `./pcpfm_filters/` (each filter defines a subset of samples, typically by mode or group) and run a sequence of PCPFM commands for each subset. The general workflow for each subset (filter) is:

1. **Assemble experiment:** Initialize a new experiment directory and sequence file for that subset of samples (using `pcpfm assemble`). This groups the data as per the filter (e.g., all samples from a specific chromatography method).
2. **Feature extraction (Asari):** Perform peak detection on the subset’s mzML files (`pcpfm asari`), generating initial feature tables using Asari’s algorithm.
3. **Build Empirical Compounds:** Group detected peaks/features into **empirical compounds** (putative metabolites) across samples (`pcpfm build_empCpds`), applying algorithms (like Khipu grouping) to consolidate features that likely represent the same compound across samples.
4. **(Optional) MS/MS mapping:** If MS² (tandem MS) data is available and filters are configured, map MS/MS spectra to the features (`pcpfm map_ms2`) for further annotation. *This step is optional and is only executed if specified; the script contains placeholders for MS2 directories.*
5. **Annotation:** Perform multi-level metabolite annotation. PCPFM supports level 4 annotation (formula or class inference) and level 2 annotation (library matching). The script runs `pcpfm l4_annotate` (e.g., using HMDB/LMSD databases) and `pcpfm l2_annotate` (e.g., using MS/MS spectral libraries like MoNA) to annotate the empirical compounds.
6. **Generate output:** Finally, create output tables (`pcpfm generate_output`) including the feature table, annotation table, and sample metadata table for the subset.

In summary, PCPFM will handle everything from raw feature detection to curated feature tables and annotations for each subset of samples. Key processing steps performed by PCPFM include:

* Peak picking and alignment across samples (via Asari) to produce high-quality feature tables.
* Data filtering, normalization, and quality control routines (e.g., blank filtering, batch correction, interpolation of missing values, etc., if configured) to refine the feature table.
* Grouping features into compounds (empirical compounds) to reduce redundancy and prepare for annotation.
* Matching features to known metabolites using MS¹ (exact mass) and MS² spectra: searching in authentic compound libraries (like HMDB, Lipid Maps) and public spectral databases (e.g., MoNA) for annotations.
* Generating standardized output files (e.g., feature matrices, compound annotation lists) and summary reports (the pipeline can produce PDFs summarizing QC metrics and results).

**Usage:** Before running this step, ensure that you have created appropriate filter JSON files in `./pcpfm_filters` for each subset of samples you want to process separately. For example, you might have filters like `HILICpos_Supernatant.json`, `HILICneg_Supernatant.json`, `RPpos_Pellet.json`, etc., which specify criteria (via sample metadata fields) to select those samples. The script will automatically process all JSON files in that directory.

Run the script with two arguments: the input CSV from Step 3 and an output prefix for the experiment names:

```bash
bash step4_pcpfm_process.sh pcpfm_sequence.csv MyExperiment
```

Here, `pcpfm_sequence.csv` is the metadata file from Step 3 (listing all samples and their mzML paths), and `"MyExperiment"` is a prefix that will be used to name output directories. The script will iterate through each filter file and process that group, creating a results directory for each (prefixed by `MyExperiment` and the filter name).

For example, if you have a filter file named `HILICpos_Supernatant.json`, the script will create an experiment directory like `./results/MyExperimentHILICpos_Supernatant/` containing the outputs for that subset. It then moves to the next filter file and repeats.

*Output:* The **`results/`** directory will contain sub-folders for each experiment (each subset defined by a filter). Within each experiment folder, you can expect to find:

* `annotations/` – containing JSON files of empirical compounds (with their detected features and any annotations).
* `asari_results/` – containing raw output from Asari, including the primary **feature table** (`preferred_Feature_table.tsv`) and potentially a full feature table under an `export/` subfolder.
* `feature_tables/` – any additional curated feature tables (if further processing or custom filtering was applied; this may be empty if not used).
* `results/` – final summary tables, such as an annotated feature table (combining feature intensities with annotations) and a sample metadata table for that experiment.

Each experiment folder name will combine the prefix you provided and the filter name (as in the example above). The output tables are ready for downstream analysis – for instance, you can take the feature table into statistical analysis or visualization workflows. The annotation table provides putative metabolite IDs for detected features, which is valuable for biological interpretation.

*Note:* The script is set up to skip certain steps for specific modes as written. For instance, in the provided script, the actual calls to `pcpfm assemble` and `pcpfm asari` are commented out, and only the later stages (compound building and annotation) are executed for some modes. In a typical run, you would ensure that all needed steps are executed (see **Notes** below about uncommenting lines or running separate commands if necessary). When fully executed, this step may take some time depending on the number of samples and data size, but it is designed to be efficient and scalable (the PCPFM pipeline was benchmarked to handle large studies with improved performance over traditional tools).

## Example Usage Summary

Bringing it all together, here is a summary of how to run the entire pipeline on your data (assuming the environment is set up and you are in the container or environment with all dependencies):

1. **Combine sequences:**

   ```bash
   python3.11 step1_combine_sequences.py
   ```

   (Reads all CSVs in `./sequences`, outputs `combined_sequences.csv`.)

2. **Add metadata:**

   ```bash
   python3.11 step2_add_pcpfm_metadata.py
   ```

   (Reads `combined_sequences.csv` and `./config/search_dict.json`, updates sample metadata in the CSV.)

3. **Map mzML files:**

   ```bash
   python3.11 step3_map_mzML.py
   ```

   (Reads `combined_sequences.csv`, finds mzML files in `../ALL_MZML/`, outputs `pcpfm_sequence.csv` with file paths.)

4. **Run PCPFM pipeline:**

   ```bash
   bash step4_pcpfm_process.sh pcpfm_sequence.csv MyExperiment
   ```

   (Processes data for each filter in `./pcpfm_filters`, results saved under `./results/` with prefix "MyExperiment".)

After these steps, check the `results/` directory for output files. You can then proceed to analyze the feature table or other outputs as needed.

## Notes and Considerations

* **Directory Structure & Paths:** The pipeline scripts assume a specific directory layout and use hard-coded relative paths. It’s recommended to run the scripts from the project root (where the scripts reside) and organize input files into the expected subdirectories:

  * `./sequences/` for input sequence CSV files,
  * `./config/` for the metadata JSON,
  * `./pcpfm_filters/` for filter JSONs,
  * an `ALL_MZML/` directory (at the same level as the pipeline directory) for mzML files.
    If your files are elsewhere, you may need to modify the path variables in the scripts (e.g., the `directory` in Step 1, `json_file_path` in Step 2, or `mzml_dir` in Step 3).

* **Step 1 – Input Format:** The combine script expects each sequence CSV to have a header row (which it skips) and columns such as **File Name** and **Instrument Method** (these are used in the script). Make sure your CSVs have consistent headers. The script will create new columns like *OriginSequence*, *Method*, and *Harvest*. If your sequence file names contain key terms (like "supernatant" or "pellet"), those will be used to classify the Harvest column. You can adjust these keywords in the script if needed.

* **Step 2 – Metadata JSON:** The metadata augmentation requires a JSON configuration (`search_dict.json`). Ensure this file exists in `./config/` and follows the expected structure. The script looks for a list of entries where each entry is either:

  * `[<Field>, <Substring>, <NewType>]` – meaning if `<Field>` contains `<Substring>`, set **Sample Type** to `<NewType>`.
  * (The code also hints at a possible 2-element form `[<Field>, <Value>]` where it would set Sample Type to that value, though the logic in code may need review.)
    Double-check that the JSON is properly formatted (e.g., an array of arrays). The script will overwrite `combined_sequences.csv` with the updated Sample Type values. If you prefer to keep the original, you might modify the script to write to a new file.

* **Step 3 – File Name Assumption:** The mzML mapping assumes that the **File Name** in the CSV matches the mzML filename. If your CSV’s File Name entries include the `.raw` extension, the script will naively append `.mzML` (resulting in names like `sample.raw.mzML`). In such cases, you should either remove the extension in the CSV beforehand or adjust the script to strip “.raw” when constructing the mzML filename. Also, the `mzml_dir` default is a directory one level up (`../ALL_MZML/`). If your mzML files are in a different location, update this path or create a symlink/placement so that path is correct. Any missing file will cause the script to throw an exception, so ensure all files are present.

* **Step 4 – Script Configuration:** The Step 4 Bash script has some parts commented out. Notably, the calls to `pcpfm assemble` and `pcpfm asari` (which perform the initial assembly and peak picking) are preceded by `#` comments in the provided script. This means if run unchanged, the script might skip directly to compound building or annotation for certain modes. **It is crucial to enable those steps** for a complete run. You should remove the comment marks (`#`) for the `pcpfm assemble` and `pcpfm asari` lines to ensure that each subset is properly initialized and processed by Asari. The script was likely tailored for a specific scenario; a fully automated run would include assemble → asari → build\_empCpds → annotate steps in sequence for each filter. Alternatively, you can manually run those commands (using `python3.11 -m pcpfm ...`) before or after running the script, if needed.

* **Step 4 – MS/MS Data Paths:** The script contains commented blocks for `pcpfm map_ms2` with specific file paths (pointing to user directories on the developer’s system). These are examples or placeholders for integrating MS² data. If you have MS/MS files (e.g., from AcquireX or other runs) that correspond to your samples, you can use `pcpfm map_ms2` to incorporate MS² matching. To do this, update those lines with the correct `--ms2_dir` pointing to your MS/MS data directories, and uncomment them for the relevant sample subsets (filters). If you do not have MS² data or do not wish to perform MS² mapping, you can leave these lines commented out. Their presence in the script is a reminder that MS² support exists, but they reference a user-specific path that **will not work in a new environment** without modification (see the AcquireX section for more details).

* **Python Version:** The pipeline was developed with Python 3.11 (the Step 4 script explicitly calls `python3.11`). In the Docker image, we ensure Python 3.11 is installed. If you run the scripts locally with a different Python 3 version, adjust the commands or create an alias so that `python3.11` invokes the correct interpreter. All code is compatible with Python 3.8+ in principle, but using the same version can avoid any subtle differences.

* **Dependencies and Performance:** Installing PCPFM via pip will pull in all required Python packages (pandas, numpy, etc.). Ensure you have sufficient memory and CPU resources allocated, especially when running via Docker, since metabolomics data processing can be intensive for large datasets. Asari is designed to handle large studies efficiently (hundreds of files), but resource limits could affect runtime. If you encounter performance issues, consider adjusting Docker resource limits or processing subsets of data sequentially.

* **Output Verification:** After the pipeline completes, take a moment to verify the outputs. Check that each expected sample is present in the feature tables, blanks/QCs are handled as intended, and annotations make sense (e.g., known standards are correctly identified). The structure of the output directories should mirror the PCPFM design (as described earlier). If something is missing, revisit the earlier steps or the filter definitions to ensure all data was included.

By following these steps and considerations, you should be able to reproduce a full metabolomics data processing workflow using Asari and PCPFM, from raw data to ready-to-analyze feature tables. This pipeline README, along with the provided Dockerfile, should help in setting up a consistent environment for analysis and sharing the workflow with others.

## Dockerfile

Below is the Dockerfile that encapsulates the above environment setup. It installs all necessary components on an Ubuntu base image and places the pipeline scripts in the container. You can use this to build the `asari_pcpfm_pipeline` image as described in the Setup section.

```Dockerfile
# Base image: Ubuntu with Python3 and required tools
FROM ubuntu:22.04

# Install system packages: Python 3.11, pip, git, wget, unzip, build tools, and Mono for RawFile conversion
RUN apt-get update && apt-get install -y \
    python3.11 python3.11-dev python3.11-distutils \
    git wget unzip build-essential mono-devel \
 && rm -rf /var/lib/apt/lists/*

# Install pip for Python 3.11
RUN wget -q https://bootstrap.pypa.io/get-pip.py && python3.11 get-pip.py && rm get-pip.py

# Install Asari and PCPFM Python packages
RUN python3.11 -m pip install --no-cache-dir asari-metabolomics pcpfm

# Install Thermo RawFileParser for .RAW to .mzML conversion
RUN mkdir -p /usr/local/thermo && \
    wget -q -O /tmp/ThermoRawFileParser.zip https://github.com/compomics/ThermoRawFileParser/releases/download/v1.4.0/ThermoRawFileParser.zip && \
    unzip /tmp/ThermoRawFileParser.zip ThermoRawFileParser.exe -d /usr/local/thermo && \
    rm /tmp/ThermoRawFileParser.zip

# Set working directory and copy pipeline scripts
WORKDIR /pipeline
COPY step1_combine_sequences.py step2_add_pcpfm_metadata.py step3_map_mzML.py step4_pcpfm_process.sh ./
RUN chmod +x step4_pcpfm_process.sh

# Default command: start an interactive shell (can be overridden)
CMD ["bash"]
```
