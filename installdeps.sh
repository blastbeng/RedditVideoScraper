#/bin/sh
export TMPDIR=/var/media/tmp
mkdir -p $TMPDIR
/usr/bin/python3.8 -m venv .venv
source .venv/bin/activate; pip3 install -r requirements.txt

rm -rf $TMPDIR/*