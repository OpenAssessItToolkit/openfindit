#!/bin/bash

if [ $# -ne 3 ]; then
    echo 'Requires: 1 site-name, 2 url, 3 path'
    exit 1
fi

NOW=$(date +"%m_%d_%Y_%H-%M")
CURRENTCSV=$1-current.csv
OLDCSV=$1-old.csv
CURRENTXLSX=$1-current.xlsx

mkdir -p "$3/$1";
mkdir -p "$3/$1/tmp/$NOW";

sleep 1


# Check if repos exist
echo "(bash) - ACTION: Checking if you have opendiffit cloned in the same level as this project."
if [ -f $(pwd)/../opendiffit/opendiffit/add_hash.py ]; then
    echo "FYI: Repo is here."
else
    echo "(bash) - HEY HUMAN: WAIT! For this demo to work, you need to git clone https://github.com/OpenAssessItToolkit/opendiffit.git at the same directory level as this project."
    exit 1
fi


# Start with xlsx if it exists, otherwise start with the csv.
if [ -f "$3/$1/$CURRENTXLSX" ]; then
    echo "(bash) - FYI: $CURRENTXLSX exists. We can start from the xlsx."
    if [ -f "$3/$1/$CURRENTCSV" ]; then
        echo "(bash) - ACTION: Archive $CURRENTCSV. We don't need it anymore."
        mv "$3/$1/$CURRENTCSV" "$3/$1/tmp/$NOW/$CURRENTCSV"
    fi
    if [ -f "$3/$1/$OLDCSV" ]; then
        echo "(bash) - ACTION: Archive $OLDCSV. We don't need it anymore."
        mv "$3/$1/$OLDCSV" "$3/$1/tmp/$NOW/$OLDCSV"
    fi
    echo "(bash) - ACTION: Convert current xls $CURRENTXLSX to $CURRENTCSV csv for processing. Continuing..."
    python3 $(pwd)/../opendiffit/opendiffit/convert_spreadsheet.py --spreadsheet="$3/$1/$CURRENTXLSX";
    sleep 3
    echo "(bash) - ACTION: Archive the current xls $CURRENTXLSX. We dont need it anymore."
    mv "$3/$1/$CURRENTXLSX" "$3/$1/tmp/$NOW/$CURRENTXLSX"
    sleep 3
else
    echo "(bash) - FYI: $CURRENTXLSX does not exists. We will start from the $CURRENTCSV csv."
fi

if [ -f "$3/$1/$OLDCSV" ]; then
    echo "(bash) - ACTION: Archive $OLDCSV We don't need it anymore."
    mv "$3/$1/$OLDCSV" "$3/$1/tmp/$NOW/$OLDCSV"
fi
if [ -f "$3/$1/$CURRENTCSV" ]; then
    echo "(bash) - FYI: $CURRENTCSV exists."
    echo "(bash) - ACTION: Convert current new csv $CURRENTCSV report to be the previous $OLDCSV csv report."
    mv "$3/$1/$CURRENTCSV" "$3/$1/$OLDCSV"
    sleep 3
fi

# Crawl site
echo "(bash) - ACTION: Crawl site to automatically create a new current report for today."
scrapy crawl findfiles -a urls="$2" -s DEPTH_LIMIT=3 -o "$3/$1/$CURRENTCSV"
sleep 3

# Check if repos exist
echo "(bash) - ACTION: Create unique hashes for files found in todays new csv $CURRENTCSV report."
# add hashes to new report
python3 $(pwd)/../opendiffit/opendiffit/add_hash.py \
--input-file="$3/$1/$CURRENTCSV" \
--output-file='-';
sleep 3

# Compare hashes and update the diff column
if [ -f "$3/$1/$OLDCSV" ] && [ -f "$3/$1/$CURRENTCSV" ]; then
    echo "(bash) - ACTION: Comparing csv files $OLDCSV with $CURRENTCSV and create/update diff column."
    python3 $(pwd)/../opendiffit/opendiffit/identify_diffs.py \
    --new="$3/$1/$CURRENTCSV" \
    --old="$3/$1/$OLDCSV" \
    --diff='-';
    sleep 3
    echo "(bash) - FYI: Comparison complete."
    echo "(bash) - HEY HUMAN: Your turn. Go manually check $CURRENTXLSX 'diff' column for NEW or UPDATED files. Test them for compliance and update the 'comply' column."
    echo "(bash) - HEY Human: Then rerun this bash script next time you want to check for new or modified PDF files."

else
    sleep 3
    echo "(bash) - HEY Human: You only have one report. We need a current and a previous to compare. Rerun this report to convert current to old."
fi

echo "(bash) - ACTION: Convert csv $CURRENTCSV back to pretty xlsx $CURRENTXLSX."
python3 $(pwd)/../opendiffit/opendiffit/convert_spreadsheet.py --spreadsheet="$3/$1/$CURRENTCSV"

if [ -f "$3/$1/$CURRENTCSV" ]; then
    echo "(bash) - ACTION: Archive $CURRENTCSV. We don't need it anymore."
    mv "$3/$1/$CURRENTCSV" "$3/$1/tmp/$NOW/$CURRENTCSV"
fi
if [ -f "$3/$1/$OLDCSV" ]; then
    echo "(bash) - ACTION: Archive $OLDCSV. We don't need it anymore."
    mv "$3/$1/$OLDCSV" "$3/$1/tmp/$NOW/$OLDCSV"
fi

echo "(bash) - FYI: Done."
