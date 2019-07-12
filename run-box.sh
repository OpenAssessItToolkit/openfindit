#!/bin/bash

if [ $# -ne 6 ]; then
    echo 'Requires: 1site-name, 2old-file, 3current-file, 4url, 5path, 6xlsx-file'
    exit 1
fi

NOW=$(date +"%m_%d_%Y_%H-%M")
# CURRENT-CSV="$1-current.csv"
# OLD-CSV="$1-old.csv"
# CURRENT-XLSX="$1-current.xlsx"

mkdir -p "$5/$1";
mkdir -p "$5/$1/tmp/$NOW";

sleep 3


# # Archive CSVs
# if [ -f "$5/$1/$6" ]; then
#     echo "(bash) - ACTION: Archive all csv files"
#     if [ -f "$5/$1/$3" ]; then
#         mv "$5/$1/$3" "$5/$1/tmp/$NOW/$3"
#     fi
#     if [ -f "$5/$1/$2" ]; then
#         mv "$5/$1/$2" "$5/$1/tmp/$NOW/$2"
#     fi
#     sleep 3
# else
#     echo "Missing xlsx file."
# fi


# Check if repos exist
echo "(bash) - ACTION: Checking if you have opendiffit cloned in the same level as this project."
if [ -f $(pwd)/../opendiffit/opendiffit/add_hash.py ]; then
    echo "FYI: Repo is here."
else
    echo "(bash) - WAIT!: For this demo to work, you need to git clone https://github.com/OpenAssessItToolkit/opendiffit.git at the same directory level as this project."
    exit 1
fi

# Check if we only have a csv to start with

# # Archive CSVs
# if [ -f "$5/$1/$2" ]; then
#     echo "(bash) - ACTION: Archive old csv $2 report."
#     mv "$5/$1/$2" "$5/$1/tmp/$NOW/$2"
#     sleep 3
# fi

# Convert XLSX to CSV
# if [ -f "$5/$1/$6" ]; then
#     echo "(bash) - ACTION: Convert current xls $6 to $3 csv for processing. Continuing..."
#     python3 $(pwd)/../opendiffit/opendiffit/convert_spreadsheet.py --spreadsheet="$5/$1/$6";
#     sleep 3
#     echo "(bash) - ACTION: Archive the current xls $6. We dont need it anymore."
#     mv "$5/$1/$6" "$5/$1/tmp/$NOW/$6"
#     sleep 3
# fi

# if [ -f "$5/$1/$2" ]; then
#     echo "(bash) - ACTION: Archiving old csv $2."
#     mv "$5/$1/$2" "$5/$1/tmp/$NOW/$2"
#     sleep 3
# fi

if [ -f "$5/$1/$3" ]; then
    echo "(bash) - ACTION: Converting current new csv $3 report to be the previous $2 csv report."
    mv "$5/$1/$3" "$5/$1/$2"
    sleep 3
fi

# Crawl site
echo "(bash) - ACTION: Crawling site to automatically create a new current report for today."
scrapy crawl findfiles -a urls="$4" -s DEPTH_LIMIT=3 -o "$5/$1/$3"
sleep 3

# Check if repos exist
echo "(bash) - ACTION: Creating unique hashes for files found in todays new csv $3 report."
# add hashes to new report
python3 $(pwd)/../opendiffit/opendiffit/add_hash.py \
--input-file="$5/$1/$3" \
--output-file='-';
sleep 3

# Compare hashes and update the diff column
if [ -f "$5/$1/$2" ] && [ -f "$5/$1/$3" ]; then
    echo "(bash) - ACTION: Comparing csv files $2 with $3 and create/update diff column."
    python3 $(pwd)/../opendiffit/opendiffit/identify_diffs.py \
    --new="$5/$1/$3" \
    --old="$5/$1/$2" \
    --diff='-';
    sleep 3

    # Convert the new csv into a xlsx
    # echo "(bash) - ACTION: Converting csv $3 back to pretty xlsx $6."
    # python3 $(pwd)/../opendiffit/opendiffit/convert_spreadsheet.py --spreadsheet="$5/$1/$3";
    sleep 3
    echo "(bash) - Process complete."
    echo "(bash) - HUMAN: Go manually check $6 'diff' column for NEW or UPDATED files. Test them for compliance and update the 'comply' column."
    echo "(bash) - Human: Then rerun run.sh next time you want to check for new or modified PDF files."

else
    echo "fuck, nothing to compare"
    # echo "(bash) - ACTION: Converting csv back to pretty $6 xlsx."
    # python3 $(pwd)/../opendiffit/opendiffit/convert_spreadsheet.py --spreadsheet="$5/$1/$3"
    sleep 3
    echo "(bash) - Process complete."
    echo "(bash) - Human: You only have one report. We need a current and a previous to compare. Rerun this report to convert current to old."
fi

# echo "(bash) - ACTION: Converting csv $3 back to pretty xlsx $6."
# python3 $(pwd)/../opendiffit/opendiffit/convert_spreadsheet.py --spreadsheet="$5/$1/$3"



# echo "(bash) - Finished."
