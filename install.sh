#!/bin/bash
##
# https://github.com/philipbergen/zero
# Licensed under terms of MIT license (see LICENSE-MIT)
# Copyright (c) 2013 Philip Bergen, philip.bergen@me.com
#
# Installs zero deps
set -eu

##
# Important directories
here="$(cd $(dirname ${BASH_SOURCE[0]}); pwd)"

##
# Returns true (0) if $1 is installed
quiet_which () {
    which $1 >/dev/null 2>&1 && return 0
    return 1
}

##
# Returns true if $1 is an installed python module
quiet_import () {
    echo "import $1" | python >/dev/null 2>&1 && return 0
    return 1
}

##
# Returns true (0) if $1 is brew installed
quiet_brewed () {
    brew info $1 >/dev/null 2>&1 || return 1
    [ "$(brew info $1 | head -3 | tail -1)" = "Not installed" ] && return 1
    return 0
}

##
# Installs Homebrew
install_libs() {
    if [ $(uname) = Darwin ]; then
        echo "*** INFO: Checking brew"
        quiet_which brew || {
            echo "*** INFO: Brew is not installed, installing."
            ruby -e "$(curl -fsSL https://raw.github.com/mxcl/homebrew/go)"
        }
        echo "*** INFO: Checking libraries"
        for a in zeromq readline ; do
            quiet_brewed $a || {
                echo "*** INFO: Missing brew $a, installing."
                brew install $a
            }
        done
        echo "*** INFO: Checkin python dependencies"
        quiet_which python || {
            echo "*** INFO: Python is not installed, installing."
            brew install python
        }
    else
        echo "*** WARNING: This is not Mac OS X. You need to install zeromq"
        echo "             using your system's installation routines or from"
        echo "             source: http://zeromq.org/intro:get-the-software"
        quiet_which python || {
            echo "*** ERROR: You will also need to install python."
            exit 1
        }
    fi
    quiet_which pip || {
        echo "*** INFO: Pip is not installed, installing."
        curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py
        echo "*** WARNING: Pip installation requires sudo, please enter sudo password:"
        sudo python get-pip.py
        rm -f get-pip.py
    }
    for mod in docopt zmq; do
        quiet_import $mod || {
            echo "*** INFO: Python module $mod is not installed, installing."
            pip install --user $mod
        }
    done
}

install_bins () {
    echo "*** INFO: Creating bin/executables"
    cd $here
    mkdir -p bin
    cd bin >/dev/null
    cat > zero <<EOF
#!/bin/bash
. $here/env.sh
python -m \$(basename \$0) "\$@"
EOF
    chmod a+x zero
    for exe in zlog zlog-sink; do
        rm -f $exe
        ln -s zero $exe
    done
    cd .. >/dev/null
    echo "*** INFO: Created" bin/*
}

##
# Creates an env.sh file to set up the proper environment to run noep in
create_env () {
    PYPKG=$(pip show pyzmq|grep Location |cut -d' ' -f2)
    echo "*** INFO: Creating env.sh."
    cat > env.sh <<EOF
export PYTHONPATH="$PYPKG:$here/py:$here/bin:$here"
export PATH="/usr/local/share/python:\$HOME/Library/Python/2.7/bin:$here/bin:\$PATH"

[ $(uname) = Darwin ] && launchctl limit maxfiles 16384
EOF
    chmod a+x env.sh
}

cd "$here"
rm -f env.py* py/docopt.py*
create_env
. ./env.sh
install_libs
install_bins

echo "*** INFO: You should source env.sh for environment correctness:"
echo "          . ./env.sh"
