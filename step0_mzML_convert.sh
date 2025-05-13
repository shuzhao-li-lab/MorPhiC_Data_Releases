find "./ALL_MZML/" -type f -name "*.raw" | xargs -P 8 -I{} mono /Users/mitchjo/Downloads/ThermoRawFileParser1.4.5/ThermoRawFileParser.exe -o . -f 2 -i "{}"
find "./ALL_MZML/" -type f -name "*.RAW" | xargs -P 8 -I{} mono /Users/mitchjo/Downloads/ThermoRawFileParser1.4.5/ThermoRawFileParser.exe -o . -f 2 -i "{}"

rm "./ALL_MZML/*.raw"
rm "./ALL_MZML/*.RAW"