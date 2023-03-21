#!/bin/bash

dir_name=${PWD##*/}
backup_dir=/var/local/backups/$dir_name
backup_name=$(date +"%Y-%m-%d.bak")

mkdir -p $backup_dir
sqlite3 db.sqlite3 ".backup '$backup_dir/$backup_name'"
