@echo off
echo =======================================================
echo PUSH DU REPO service-comm-benchmark VERS GITHUB
echo =======================================================
cd /d "%~dp0"
echo Verification de la configuration Git...
git remote -v
echo.
echo Envoi des commits sur la branche main...
git push -u origin main
echo.
if %ERRORLEVEL% EQU 0 (
    echo [SUCCES] Le repo a ete pousse avec succes sur GitHub !
    echo Lien public : https://github.com/Tony-UY/service-comm-benchmark
) else (
    echo [ATTENTION] Le push a echoue.
    echo Avez-vous cree le repository public vide 'service-comm-benchmark' sur https://github.com/new ?
    echo Une fois cree sur GitHub, relancez ce script !
)
pause
