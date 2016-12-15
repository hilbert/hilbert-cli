#! /bin/bash

WORKDIR="$HOME"

SELFDIR=`dirname "$0"`
SELFDIR=`cd "$SELFDIR" && pwd`

cd "${WORKDIR}"

HTTP_PORT="${HTTP_PORT:-8080}"
python2.7 -c "import SimpleHTTPServer,BaseHTTPServer; BaseHTTPServer.HTTPServer((\"\", ${HTTP_PORT}), SimpleHTTPServer.SimpleHTTPRequestHandler).serve_forever()"
