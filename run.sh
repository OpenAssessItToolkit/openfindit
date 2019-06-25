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
CURRENT=docs/assets/alice__current.csv
PREV=docs/assets/alice__prev.csv

if [ -f "docs/assets/alice__prev.csv" ]; then
    echo "a docs/assets/alice__prev.csv csv report exists. Continue..."
else
    echo "b docs/assets/alice__prev.csv does not exist."

    if [ -f "docs/assets/alice__current.csv" ]; then
        echo "c There is a current csv report. Automatically convert docs/assets/alice__current.csv to docs/assets/alice__prev.csv."
        mv 'docs/assets/alice__current.csv' 'docs/assets/alice__prev.csv';
    else
        echo "d No csv reports exists to compare. You should run a new one."
    fi
fi

if [ -f "docs/assets/alice__current.csv" ]; then
    echo "e docs/assets/alice__current.csv csv report exists. Continue..."
    python3 ../opendiffit/opendiffit/add_hash.py \
    --input-file='docs/assets/alice__current.csv' \
    --output-file='-';
else
    echo "f docs/assets/alice__current.csv csv report does not exist. Creating a new csv report."
    echo "g Crawling site"
    scrapy crawl findfiles -a urls='https://openassessittoolkit.github.io/openfindit/pdf-test-page.html' -s DEPTH_LIMIT=1 -o 'docs/assets/alice__current.csv';

    echo "h Hashing files found in the new report"
    python3 ../opendiffit/opendiffit/add_hash.py \
    --input-file='docs/assets/alice__current.csv' \
    --output-file='-';
fi

# read -p "Crawl site" -t 1;
# scrapy crawl findfiles -a urls='$SITE' -s DEPTH_LIMIT=1 -o '/Users/joel/Desktop/spy/wiki__current.csv';

# read -p "Hashing files found in the report" -t 1;
# python3 ../opendiffit/opendiffit/add_hash.py \
# --input-file='/Users/joel/Desktop/spy/wiki__current.csv'\
# --output-file='-';

echo "i Compare csv reports"

if [ -f "docs/assets/alice__prev.csv" ]; then
    echo "j docs/assets/alice__prev.csv csv report exists. Continue..."
    python3 ../opendiffit/opendiffit/identify_diffs.py --old='docs/assets/alice__prev.csv' --new='docs/assets/alice__current.csv' --diff='-';
else
    echo "k docs/assets/alice__prev.csv does not exist. We need two files to create a diff."
    echo "Rerun this thing. We will convert the current one to a prev for you."
    exit
fi


# read -p "Delete previous csv report and rename as previous csv report." -t 1;
# rm -f /Users/joel/Desktop/spy/wikispy__prev.csv;
# cp '/Users/joel/Desktop/spy/wiki__current.csv' '/Users/joel/Desktop/spy/wiki__prev.csv';

echo "j Human: Go manually check NEW or UPDATED files for compliance and update the comply column."
echo "k Ready to run again."
echo "l Complete";