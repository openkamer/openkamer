python -m venv env
CALL env\Scripts\activate.bat
python -m pip install -U pip
powershell -Command "(New-Object Net.WebClient).DownloadFile('http://ftp.esrf.eu/pub/scisoft/silx/wheelhouse/lxml-3.6.0-cp35-cp35m-win_amd64.whl', 'lxml-3.6.0-cp35-cp35m-win_amd64.whl')"
pip install lxml-3.6.0-cp35-cp35m-win_amd64.whl
del lxml-3.6.0-cp35-cp35m-win_amd64.whl
pip install -r requirements.txt
python create_local_settings.py
python manage.py migrate
