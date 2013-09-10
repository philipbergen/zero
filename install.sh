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
    quiet_import clint || {
        echo "*** INFO: Python module clint is not installed, installing."
        pip install --user clint
    }
    quiet_import zmq || {
        echo "*** INFO: Python module pyzmq is not installed, installing."
        pip install --user pyzmq
    }
    if [ ! -f $here/py/docopt.py ]; then
        echo "*** INFO: Python module docopt is not installed, installing into $here/py."
        curl https://raw.github.com/docopt/docopt/master/docopt.py > $here/py/docopt.py
    fi
}

install_bins () {
    echo "*** INFO: Creating bin/executables"
    cd $here
    mkdir -p bin
    cd bin
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
    cd ..
    echo "*** INFO: Created" bin/*
}

##
# Creates an env.sh file to set up the proper environment to run noep in
create_env () {
    echo "*** INFO: Creating env.sh. Use . ./env.sh to set up the noep environment."
    cat > env.sh <<EOF
export PYTHONPATH="/usr/local/lib/python2.7/site-packages:/Library/Python/2.7/site-packages:$here/py:$here/bin:$here"
export PATH="/usr/local/share/python:\$HOME/Library/Python/2.7/bin:$here/bin:\$PATH"

[ $(uname) = Darwin ] && launchctl limit maxfiles 16384
EOF
    chmod a+x env.sh
    echo "*** INFO: Creating env.py."
    cat > env.py <<EOF
HERE = '$here'
BIN = HERE + '/bin'
HOSTNAME = '$(hostname -f)'
EOF
}

cd "$here"
create_env
. ./env.sh
echo "*** INFO: You should source env.sh for environment correctness"
install_libs
install_bins
