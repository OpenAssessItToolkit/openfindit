#!/bin/bash

# if [ $# -ne 4 ]; then
#     echo 'Requires: url, output filename, webdriver'
#     exit 1
# fi
# mkdir -p $(pwd)/tmp/$3;
# $1 $2 \

# pip install -r ../opendiffit/requirements.txt
# mkdir -p ~/Desktop/spy;
# rm -f /Users/joel/Desktop/spy/wikispy.csv

SITE=https://openassessittoolkit.github.io/openfindit/pdf-test-page.html
CURRENT=docs/assets/alice_today.csv
PREV=docs/assets/alice_prev.csv

if [ -f "docs/assets/alice_prev.csv" ]; then
    echo "(bash) - FYI: You have an old report we don't need anymore. Continuing..."
    echo "(bash) - ACTION: Removing old alice_prev.csv report."
    rm 'docs/assets/alice_prev.csv'
fi

if [ -f "docs/assets/alice_today.csv" ]; then
    echo "(bash) - ACTION: Converting alice_today.csv report to be the previous alice_prev.csv report."
    mv 'docs/assets/alice_today.csv' 'docs/assets/alice_prev.csv';
fi

echo "(bash) - ACTION: Crawling site to automatically create a current report for today."
scrapy crawl findfiles -a urls='https://openassessittoolkit.github.io/openfindit/pdf-test-page.html' -s DEPTH_LIMIT=1 -o 'docs/assets/alice_today.csv'
echo "(bash) - ACTION: Creating unique hashes for files found in todays new alice_today.csv report."
python3 ../opendiffit/opendiffit/add_hash.py \
--input-file='docs/assets/alice_today.csv' \
--output-file='-';

if [ -f "docs/assets/alice_prev.csv" ] && [ -f "docs/assets/alice_prev.csv" ]; then
    echo "(bash) - ACTION: Comparing files and create/update diff column."
    python3 ../opendiffit/opendiffit/identify_diffs.py \
    --new='docs/assets/alice_today.csv' \
    --old='docs/assets/alice_prev.csv' \
    --diff='-';
    echo "(bash) - HUMAN: Go manually check alice_today.csv 'diff' column for NEW or UPDATED files. Test them for compliance and update the 'comply' column."
    echo "(bash) - Human: Then rerun bash.sh next time you want to check for new or modified PDF files."
else
    echo "(bash) - Human: You only have one report. We need a current and a previous to compare. Rerun this report to convert current to old."
    exit 1
fi
echo "(bash) - Done."
