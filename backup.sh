#!/bin/bash

dir_path=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
dir_name=$( basename $dir_path )
backup_dir=/var/local/backups/$dir_name
backup_name=$( date +"%Y-%m-%d.bak" )

mkdir -p $backup_dir
sqlite3 db.sqlite3 ".backup '$backup_dir/$backup_name'"
