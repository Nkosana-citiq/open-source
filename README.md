# open_source

```bash
#clone the repo
git clone git@github.com:Nkosana-citiq/open-source.git
#setup the virtualenv
cd open_source
virtualenv -p python3 venv(currently on python3.6)
source venv/bin/activate
#install dependencies
pip install -e .
#start the service on localhost
gunicorn open_source.rest_service:api --workers 2 --bind 127.0.0.1:8009 --timeout 90 --log-level DEBUG

```
