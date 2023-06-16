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

info "ensure project directories have correct ownership and permissions:"
sudo mkdir -pv /srv/www/$1                     # create project directory
touch /srv/www/$1/db.sqlite3                   # create db.sqlite3 file
sudo mkdir -pv /srv/www/$1/static              # initialize static directory
sudo mkdir -pv /srv/www/$1/media               # init media dir
sudo chown -Rv $user:www-data /srv/www/$1      # change group ownership to www-data
sudo chmod -v g+w /srv/www/$1/db.sqlite3       # allow www-data to write to db.sqlite3
sudo chmod -v g+w /srv/www/$1/media            # allow www-data to write to media dir

info "create gunicorn log directory:"
sudo mkdir -pv /var/log/gunicorn
sudo chown -Rv $user:www-data /var/log/gunicorn
sudo chmod -v g+w /var/log/gunicorn

info "all done, don't forget to set env vars"
