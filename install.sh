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
    mod=$1
    pip=$mod
    [ "$mod" = zmq ] && pip=pyzmq
    pip show $pip | grep -q '^Location:' && return 0
    echo "import $mod" | python >/dev/null 2>&1 && return 0
    return 1
}

##
# Makes sure there is pip and python on the system
install_pip() {
    quiet_which python || {
        echo "*** ERROR: python is required"
        exit 1
    }
    quiet_which pip || {
        echo "*** INFO: Pip is not installed, installing."
        curl -O https://raw.github.com/pypa/pip/master/contrib/get-pip.py
        echo "*** WARNING: Pip installation requires sudo, please enter sudo password:"
        sudo python get-pip.py
        rm -f get-pip.py*
    }
}

##
# With pip install required python modules.
install_libs() {
    quiet_import zmq || {
        echo "*** INFO: Installing missing python module pyzmq"
        pip install --egg --user --install-option=--zmq=bundled --install-option=--prefix= pyzmq
    }
    for mod in docopt; do
        quiet_import $mod || {
            echo "*** INFO: Python module $mod is not installed, installing."
            pip install --egg --user --install-option=--prefix= $mod
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
# Creates an env.sh file to set up the proper environment to run zero in
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
install_pip
create_env
. ./env.sh
install_libs
install_bins
