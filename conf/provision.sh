#!/bin/bash

set -e

sudo apt-get update
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
   build-essential git gettext \
   python-virtualenv curl yui-compressor python-dev \
   libpq-dev libxml2-dev libxslt-dev libffi-dev \
   libjpeg-dev screen \
   libyaml-dev >/dev/null


grep -qG 'cd $HOME/yournextmp' "$HOME/.bashrc" ||
   cat <<'EOF' >> "$HOME/.bashrc"

source ~/yournextmp/venv/bin/activate
cd ~/yournextmp
EOF
source "$HOME/.bashrc"

cd ~/yournextmp
yournextrepresentative/bin/pre-deploy
