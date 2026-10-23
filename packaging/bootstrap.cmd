@echo off
setlocal
set "UV_PYTHON_INSTALL_DIR=%~1\python"
set "UV_PYTHON_INSTALL_BIN=0"
set "UV_PROJECT_ENVIRONMENT=%~1\.venv"
set "UV_HTTP_RETRIES=0"
set "UV_LINK_MODE=copy"
"%~dp0tools\uv.exe" sync --project "%~dp0." --locked --no-dev --no-install-project --python 3.12.10 --managed-python --no-cache
exit /b %errorlevel%
