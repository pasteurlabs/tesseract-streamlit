#!/usr/bin/env bash

# the parent dir of this script:
scriptdir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# a temporary dir to store the downloads for the example:
tmpdir=$(mktemp -d)

# clone tesseract-core for its example subdirectory:
git clone --depth 1 --branch v0.9.0 https://github.com/pasteurlabs/tesseract-core.git "${tmpdir}/tesseract-core"

# install requirements for the udf.py module:
pip install -r "${scriptdir}/requirements.txt"

# build and serve the vectoradd_jax example tesseract:
example=vectoradd_jax
tesseract build "${tmpdir}/tesseract-core/examples/${example}"
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
