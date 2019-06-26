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
    echo "(bash) - FYI: alice_prev.csv csv report exists. Continuing..."
else
    echo "(bash) - FYI: alice_prev.csv does not exist."

    if [ -f "docs/assets/alice_today.csv" ]; then
        echo "(bash) ACTION: Renaming 'alice_today.csv to alice_prev.csv."
        mv 'docs/assets/alice_today.csv' 'docs/assets/alice_prev.csv';
    else
        echo "(bash) - FYI: No csv reports exists to compare. You should run a new one."
    fi
fi

if [ -f "docs/assets/alice_today.csv" ]; then
    echo "(bash) - FYI: alice_today.csv csv report exists. Continuing..."
    python3 ../opendiffit/opendiffit/add_hash.py \
    --input-file='docs/assets/alice_today.csv' \
    --output-file='-';
else
    echo "(bash) - FYI: alice_today.csv csv report does not exist."
    echo "(bash) - ACTION: Crawling site to automatically create a current report for today."
    scrapy crawl findfiles -a urls='https://openassessittoolkit.github.io/openfindit/pdf-test-page.html' -s DEPTH_LIMIT=1 -o 'docs/assets/alice_today.csv';

    python3 ../opendiffit/opendiffit/add_hash.py \
    --input-file='docs/assets/alice_today.csv' \
    --output-file='-';

    echo "(bash) - ACTION: Creating unique hashes for files found in the todays new alice_today.csv report."
fi

echo "(bash) ACTION: Comparing the old alice_prev.csv report to todays new alice_today.csv report"

if [ -f "docs/assets/alice_prev.csv" ]; then
    echo "(bash) - FYI: old alice_prev.csv does not exist. We need two files to create a diff."
    echo "(bash) - HUMAN: Rerun this bash.sh script. We will convert the current one to a prev and run the report again."
    exit
fi

echo "(bash) - FYI: Complete."
echo "(bash) - HUMAN: Go manually check NEW or UPDATED files for compliance and update the 'comply' column."