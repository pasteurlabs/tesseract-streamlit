#!/usr/bin/env bash

# the parent dir of this script:
scriptdir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workdir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# a temporary dir to store the downloads for the example:
tmpdir=$(mktemp -d)

if [ "$(basename $workdir)" != "tesseract-streamlit" ]; then
    echo "Path mismatch: please contact the developers."
    echo $workdir
    exit 1
fi

# install requirements for the udf.py module:
pip install -r "${scriptdir}/requirements.txt"

# build and serve the vectoradd_jax example tesseract:
example=jax_fem
tesseract build "${workdir}/examples/${example}"
tessinfo=$(tesseract serve $example)
tessid=$(echo $tessinfo | jq -r '.project_id')
tessport=$(echo $tessinfo | jq -r '.containers[0].port')

# automatically generate the Streamlit app from the served tesseract:
tesseract-streamlit --user-code "${scriptdir}/udf.py" "http://localhost:${tessport}" "${tmpdir}/app.py"

# launch the web-app:
streamlit run "${tmpdir}/app.py"

# stop serving the tesseract
tesseract teardown $tessid

# clean up the temporary directory:
rm -rf $tmpdir

exit 0
