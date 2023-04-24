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
    help_print "Usage: setup.sh [OPTION] HOSTNAME"
    help_print "Prepare the directoy /srv/www/HOSTNAME for deployment of LyProX"
    help_print
    help_print "Options:"
    help_print "  -h          Display this help text"
    help_print "  -b BRANCH   Git revision of the LyProX repo to check out (default: main)"
    help_print "  -p VERSION  Python version to use for .venv (default: 3.8)"
}

prep_dir() {
    sudo mkdir -p $1
    sudo chown -R $user:www-data $1

    if [[ $2 == "add_write" ]]; then
        sudo find $1 -exec chmod g+w {} \;
    else
        sudo find $1 -exec chmod g-w {} \;
    fi
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

info "clone LyProX repo into correct location:"
if [[ ! -d /srv/www/$1/.git ]]; then
    git clone --branch $branch https://github.com/rmnldwg/lyprox /srv/www/$1
fi
git --git-dir=/srv/www/$1/.git --work-tree=/srv/www/$1 checkout --force $branch
git --git-dir=/srv/www/$1/.git --work-tree=/srv/www/$1 pull --force

info "create .venv and install dependencies:"
eval "python$py_version -m venv /srv/www/$1/.venv"
python=/srv/www/$1/.venv/bin/python
eval "$python -m pip install -U pip setuptools setuptools_scm wheel"
eval "$python -m pip install /srv/www/$1"

info "ensure all directories have correct ownership and permissions:"
touch /srv/www/$1/db.sqlite3            # create db.sqlite3 file
prep_dir /srv/www/$1                    # change group ownership to www-data
prep_dir /srv/www/$1/static             # initialize static directory
prep_dir /srv/www/$1/media add_write    # init media dir and allow write access
sudo chmod 664 /srv/www/$1/db.sqlite3   # allow www-data to write to db.sqlite3
prep_dir /srv/www/$1/.venv              # change group owner to allow www-data to execute .venv
prep_dir /var/log/gunicorn add_write    # allow www-data to write to log dir

info "all done, don't forget to set env vars"
