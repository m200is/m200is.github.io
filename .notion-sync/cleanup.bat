@echo off
REM 불필요한 파일 정리 스크립트

echo Notion sync 관련 불필요한 파일 삭제 중...

del /F /Q examples.py 2>nul
del /F /Q NOTION_TO_GITHUB.md 2>nul
del /F /Q SETUP_SUMMARY.md 2>nul
del /F /Q requirements.txt 2>nul
del /F /Q setup.bat 2>nul
del /F /Q setup.sh 2>nul

echo 완료!
echo.
echo 이제 깔끔해진 상태입니다.
echo .notion-sync/ 폴더에 필요한 파일들만 있습니다.

pause
