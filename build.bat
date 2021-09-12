@echo off
setlocal

echo "Installing python build package..."
python -m pip install --upgrade build

echo "Building app..."
python -m build

echo "Done."

SET /P UPLOAD=Upload package (Y/[N])?
IF /I "%UPLOAD%" NEQ "Y" GOTO END

echo "Installing twine..."
python -m pip install --upgrade twine

SET /P UPLOAD=Test Upload (Y/[N])?
IF /I "%UPLOAD%" NEQ "Y" GOTO PYPI_REPOSITORY

SET UPLOAD_REPOSITORY=testpypi
GOTO UPLOAD

:PYPI_REPOSITORY
SET UPLOAD_REPOSITORY=pypi
GOTO UPLOAD

:UPLOAD
echo "Uploading"
python -m twine upload --repository "%UPLOAD_REPOSITORY%" "./dist/*"

:END
endlocal

pause