@echo off
title Student Result Analysis System - Web
cd /d "%~dp0"
where py >nul 2>nul && (set PY=py) || (set PY=python)
echo Installing requirements (the first run takes a minute)...
%PY% -m pip install --quiet --disable-pip-version-check -r requirements.txt
echo Starting the web app at http://localhost:8501  (close this window to stop it)
%PY% -m streamlit run streamlit_app.py
pause
