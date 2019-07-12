#!/bin/bash
if [ $# -ne 4 ]; then
    echo 'Requires: site-name, old-file, new-file, url'
    exit 1
fi

mkdir -p $(pwd)/tmp/$1;

if [ -f $(pwd)/tmp/$1/$2 ]; then
    echo "(bash) - FYI: You have an old report we don't need anymore. Continuing..."
    echo "(bash) - ACTION: Removing old $2 report."
    rm $(pwd)/tmp/$1/$2
fi

if [ -f $(pwd)/tmp/$1/$3 ]; then
    echo "(bash) - ACTION: Converting $1_today.csv report to be the previous $2 report."
    mv $(pwd)/tmp/$1/$3 $(pwd)/tmp/$1/$2;
fi

echo "(bash) - ACTION: Crawling site to automatically create a current report for today."
scrapy crawl findfiles -a urls=$4 -s DEPTH_LIMIT=1 -o $(pwd)/tmp/$1/$3

echo "(bash) - ACTION: Checking if you have opendiffit cloned in the same level as this project."
if [ -f $(pwd)/../opendiffit/opendiffit/add_hash.py ]; then
    echo "(bash) - ACTION: Creating unique hashes for files found in todays new $3 report."
    python3 $(pwd)/../opendiffit/opendiffit/add_hash.py \
    --input-file=$(pwd)/tmp/$1/$3 \
    --output-file='-';
else
    echo "(bash) - WAIT!: For this demo to work, you need to git clone https://github.com/OpenAssessItToolkit/opendiffit.git at the same directory level as this project."
    exit 1

fi

if [ -f $(pwd)/tmp/$1/$2 ] && [ -f $(pwd)/tmp/$1/$3 ]; then
    echo "(bash) - ACTION: Comparing files and create/update diff column."
    python3 $(pwd)/../opendiffit/opendiffit/identify_diffs.py \
    --new=$(pwd)/tmp/$1/$3 \
    --old=$(pwd)/tmp/$1/$2 \
    --diff='-';
    echo "(bash) - HUMAN: Go manually check $3 'diff' column for NEW or UPDATED files. Test them for compliance and update the 'comply' column."
    echo "(bash) - Human: Then rerun run.sh next time you want to check for new or modified PDF files."
else
    echo "(bash) - Human: You only have one report. We need a current and a previous to compare. Rerun this report to convert current to old."
    exit 1
fi
echo "(bash) - Done."
