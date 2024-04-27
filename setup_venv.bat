@echo off
py -3.11 -m pip install --upgrade pip
py -3.11 -m venv .venv
.venv\scripts\activate && pip install -r requirements.txt
