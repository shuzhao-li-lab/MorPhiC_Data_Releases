import pandas as pd
import argparse
from mass2chem.formula import calculate_formula_mass

def calculate_derivative_masses(steroid_csv, group_mass, group_name):
    steroids_df = pd.read_csv(steroid_csv)
    derivatives = []

    for _, row in steroids_df.iterrows():
        formula = row['formula']
        base_mass = calculate_formula_mass(formula)
        for groups_added in range(0, 4):  # Updated to include 0 groups
            total_mass = base_mass + groups_added * group_mass
            derivative = {
                'steroid': row['steroid'],
                'groups_added': groups_added,
                'group_name': group_name,
                'derivative_mass': total_mass
            }
            derivatives.append(derivative)

    return pd.DataFrame(derivatives)


def annotate_features(feature_tsv, derivatives_df, ppm_tolerance=10):
    features_df = pd.read_csv(feature_tsv, sep='\t')

    mzml_cols_standards = [x for x in features_df.columns if "Standard_12C_" in x]
    annotations = []
    annotation_df = []
    for _, feature in features_df.iterrows():
        mz = feature['mz']
        matches = []

        for _, derivative in derivatives_df.iterrows():
            expected_mass = derivative['derivative_mass'] + 1.00727647 
            tolerance = expected_mass * ppm_tolerance / 1e6
            
            if abs(mz - expected_mass) <= tolerance:
                if all(feature[file] > 0 for file in mzml_cols_standards):
                    match = f"{derivative['steroid']}+{derivative['groups_added']}{derivative['group_name']}"
                    matches.append(match)
                    print(match)
        annotation_df.append({'mz': feature['mz'], 'id_number': feature['id_number'], 'annotation': ';'.join(matches)})
    return pd.DataFrame(annotation_df)


if __name__ == '__main__':
    derivatives_df_dncl = calculate_derivative_masses('steroids.csv', 233.05105, "DnCl")
    derivatives_df_dnhz = calculate_derivative_masses('steroids.csv', 247.07793, "DnHz")

    annotated_df_dncl_pel = annotate_features("/Users/mitchjo/Downloads/MorPhiC_Data_Release_05_13_2025/Metabolomics3/results/Metabolomics3DnCl_Pellet/output/feature_table.tsv", derivatives_df_dncl)
    annotated_df_dnhz_pel = annotate_features("/Users/mitchjo/Downloads/MorPhiC_Data_Release_05_13_2025/Metabolomics3/results/Metabolomics3DnHz_Pellet/output/feature_table.tsv", derivatives_df_dnhz)
    annotated_df_dncl_sup = annotate_features("/Users/mitchjo/Downloads/MorPhiC_Data_Release_05_13_2025/Metabolomics3/results/Metabolomics3DnCl_Supernatant/output/feature_table.tsv", derivatives_df_dncl)
    annotated_df_dnhz_sup = annotate_features("/Users/mitchjo/Downloads/MorPhiC_Data_Release_05_13_2025/Metabolomics3/results/Metabolomics3DnHz_Supernatant/output/feature_table.tsv", derivatives_df_dnhz)
    
    
    annotated_df_dncl_pel.to_csv("/Users/mitchjo/Downloads/MorPhiC_Data_Release_05_13_2025/Metabolomics3/results/Metabolomics3DnCl_Pellet/output/annotation_table.tsv", sep='\t', index=False)
    annotated_df_dnhz_pel.to_csv("/Users/mitchjo/Downloads/MorPhiC_Data_Release_05_13_2025/Metabolomics3/results/Metabolomics3DnHz_Pellet/output/annotation_table.tsv", sep='\t', index=False)
    annotated_df_dncl_sup.to_csv("/Users/mitchjo/Downloads/MorPhiC_Data_Release_05_13_2025/Metabolomics3/results/Metabolomics3DnCl_Supernatant/output/annotation_table.tsv", sep='\t', index=False)
    annotated_df_dnhz_sup.to_csv("/Users/mitchjo/Downloads/MorPhiC_Data_Release_05_13_2025/Metabolomics3/results/Metabolomics3DnHz_Supernatant/output/annotation_table.tsv", sep='\t', index=False)