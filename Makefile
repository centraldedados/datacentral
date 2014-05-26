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


run:
	python generate.py

runoffline:
	python generate.py --offline

install:
	virtualenv venv --no-site-packages --distribute --prompt=datacentral
	. `pwd`/.env ; pip install -r requirements.txt

serve:
	cd _output && python -m SimpleHTTPServer

upload:
	rsync --compress --progress --recursive --update --delete _output/* wf:~/webapps/centraldedados/
