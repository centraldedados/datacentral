# Project : Data Central
# -----------------------------------------------------------------------------
# Author : Ricardo Lafuente <r@manufacturaindependente.org>
# -----------------------------------------------------------------------------
# License : GNU General Public License
# -----------------------------------------------------------------------------
# This file is part of the Data Central package.
#
# Data Central is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Data Central is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Data Central. If not, see <http://www.gnu.org/licenses/>.

# This is *heavily* based on Edouard Richard's excellent Makefiles.
# See https://github.com/jplusplus/resonate2014/blob/master/Makefile for
# the basis from where this file was created.

# your SSH target dir for rsync (set this in the environment)
#SSH_PATH = "wf:~/webapps/centraldedados/"

# server port for local server
SERVER_PORT = 8002
MAIN_SCRIPT = $(wildcard datacentral.py)
OFFLINE_FLAG = "--offline"
OUTPUT = "_output"


all: build

build:
	. `pwd`/.env/bin/activate; python $(MAIN_SCRIPT)

build-offline:
	. `pwd`/.env/bin/activate; python $(MAIN_SCRIPT) $(OFFLINE_FLAG)

install:
	if ! [ -x "$(pyvenv -h)" ]; then virtualenv .env --no-site-packages --distribute --prompt=\(datacentral\); else pyvenv .env; fi
	. `pwd`/.env/bin/activate; pip install -r requirements.txt
	if [ ! -f settings.conf ]; then cp settings.conf.sample settings.conf; fi

serve:
	. `pwd`/.env/bin/activate; livereload -p $(SERVER_PORT) $(OUTPUT)

deploy:
	rsync --checksum --compress --progress --recursive --delete $(OUTPUT)/ $(SSH_PATH)

deploy-dry:
	rsync --dry-run --checksum --compress --progress --recursive --delete $(OUTPUT)/ $(SSH_PATH)

clean:
	rm -fr repos $(OUTPUT)

test:
	. `pwd`/.env/bin/activate; nosetests tests.py
