@echo off
setlocal
if exist "..\state\openclaw.json" del /q "..\state\openclaw.json"
if exist "..\state\.env" del /q "..\state\.env"
echo OpenClaw Portable configuration has been reset.
