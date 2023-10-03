#!bash
#
# Copyright 2019 - 2023
# Andr\xe9 Malo or his licensors, as applicable
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

set -e

# Parse arguments
want_python=
want_upgrade=
while getopts "pu" opt; do
    case "${opt}" in
        p) want_python=1 ;;
        u) want_upgrade=1 ;;
        *) die "Unknown option -${opt}" ;;
    esac
done
shift "$((OPTIND - 1))"

dir="${1}"
shift

[ -n "${VIRTUAL_ENV}" ]
[ -n "${dir}" ]

source "${VIRTUAL_ENV}/bin/activate"

if [ "${want_python}" = "1" ]; then
    (
        set -e

        cd "${VIRTUAL_ENV}"
        mkvirtualenv --clear --python \
            "$(pyv="$(python -c 'import sys; print("python" + ".".join(map(str, sys.version_info[:2])))')"; \
            deactivate; which "${pyv}")" .
    ) || exit $?
fi

cd "${dir}"
pip freeze | grep -v '^-e ' | while read file; do
    pip uninstall -y "${file}"
done

upgrade=()
if [ "${want_upgrade}" = "1" ]; then
    upgrade=( "-U" )
fi
pip install "${upgrade[@]}" setuptools pip
pip install "${upgrade[@]}" -r development.txt
