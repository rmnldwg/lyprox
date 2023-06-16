#!/bin/bash

# ask user for confirmation and delete the db.sqlite3 file
read -n 1 -r -e -p "Are you sure you want to delete the database? [y/N] "

if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm db.sqlite3
    rm -rf ./media/risk
    rm -rf ./media/source
fi
