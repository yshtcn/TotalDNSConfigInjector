@echo off
@echo start
cd /d %~dp0
py dns_query.py config_Parsec.ini
pause
