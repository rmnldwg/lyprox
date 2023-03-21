#!/bin/bash

user=${SUDO_USER:-$USER}
width=$(eval "tput cols")
color=$(tput setaf 4)
normal=$(tput sgr0)

info() {
    printf "%s\n" "${color}$1${normal}"
}

help_print() {
    printf "%s\n" "${normal}$1"
}

help() {
    help_print "Usage: deploy [OPTION] HOSTNAME"
    help_print "Prepare the directoy /srv/www/HOSTNAME for deployment of LyProX"
    help_print
    help_print "Options:"
    help_print "  -h          Display this help text"
    help_print "  -b BRANCH   Git revision of the LyProX repo to check out (default: main)"
    help_print "  -p VERSION  Python version to use for .venv (default: 3.8)"
}

prep_dir() {
    if [ $2 == "write" ]; then
        permissions=664
    else
        permissions=644
    fi
    mkdir -p $1
    chown -R $user:www-data $1
    find $1 -type d -exec chmod $(($permissions + 111)) {} \;
    find $1 -type f -exec chmod $permissions {} \;
}

while getopts ":hb:p:" option; do
    case $option in
        h)
            help
            exit;;
        b)
            branch=$OPTARG
            ;;
        :)
            info "Missing argument for option -b"
            exit 1;;
        p)
            py_version=$OPTARG
            ;;
        :)
            info "Missing argument for option -p"
            exit 1;;
        \?)
            info "Invalid option"
            exit 1;;
    esac
done
shift $((OPTIND - 1))
branch=${branch:-main}
py_version=${py_version:-3.8}

info "create log directories and assign correct permissions:"
prep_dir /var/log/gunicorn write

info "clone LyProX repo into correct location:"
if [ ! -d /srv/www/$1/.git ]; then
    git clone --depth=1 --branch $branch https://github.com/rmnldwg/lyprox /srv/www/$1
fi
git --git-dir=/srv/www/$1/.git --work-tree=/srv/www/$1 checkout --force $branch
git --git-dir=/srv/www/$1/.git --work-tree=/srv/www/$1 pull --depth=1 --force

info "create srv directory and assign correct permissions:"
prep_dir /srv/www/$1 read
chmod 775 /srv/www/$1
prep_dir /srv/www/$1/static read
prep_dir /srv/www/$1/media write
chmod 664 /srv/www/$1/db.sqlite3

info "create .venv and install dependencies:"
eval "python$py_version -m venv /srv/www/$1/.venv"
python=/srv/www/$1/.venv/bin/python
eval "$python -m pip install -U pip setuptools setuptools_scm wheel"
eval "$python -m pip install /srv/www/$1"

info "all done, don't forget to set env vars:"
