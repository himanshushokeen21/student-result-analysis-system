@echo off
title Student Result Analysis System
cd /d "%~dp0"
where py >nul 2>nul && (set PY=py) || (set PY=python)
if not exist result_analysis.db %PY% seed_data.py
%PY% result_analysis_system.py
pause
