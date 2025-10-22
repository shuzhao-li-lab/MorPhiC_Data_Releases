#!/bin/bash
CSV=$1
OUTPUT=$2
BASE="./results/"
FILTERS="./pcpfm_filters/"

if [ -z "$CSV" ] || [ -z "$OUTPUT" ]; then
    echo "Usage: $0 <INPUT_CSV> <OUTPUT_PREFIX>" >&2
    exit 1
fi

run() {
    MODE=$1
    FILTER=$2
    EXPERIMENT="$BASE$OUTPUT$MODE"

    python3.11 -m pcpfm assemble -o $BASE -j $OUTPUT$MODE -s $CSV --filter=$FILTER --path_field mzml_path --name_field "File Name"

    if [[ $MODE =~ (DnHz|dnhz|DnCl|dncl) ]]; then
        python3.11 -m pcpfm assemble -o $BASE -j $OUTPUT$MODE -s $CSV --filter=$FILTER --path_field mzml_path --name_field "File Name"
        python3.11 -m pcpfm asari -i $EXPERIMENT --extra_asari "--min_peak_height 500000 --min_intensity_threshold 500000"
        python3.11 -m pcpfm build_empCpds -i $EXPERIMENT -tm preferred -em preferred --add_singletons=True
        python3.11 -m pcpfm generate_output -i $EXPERIMENT -em preferred -tm preferred 
    else
        python3.11 -m pcpfm l4_annotate -i $EXPERIMENT -em preferred_map -nm HMDB_LMSD_annotated_preferred
        python3.11 -m pcpfm l2_annotate -i $EXPERIMENT -em HMDB_LMSD_annotated_preferred -nm HMDB_LMSD_MoNA_annotated_preferred
        python3.11 -m pcpfm generate_output -i $EXPERIMENT -em HMDB_LMSD_MoNA_annotated_preferred -tm preferred_map

    fi
}

for file in $FILTERS*.json; do
    MODE=$(basename "$file" .json)
    run "$MODE" "$file"
done