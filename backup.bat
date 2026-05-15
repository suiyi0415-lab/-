@echo off
chcp 65001 >nul
echo ==== 开始自动备份到 Gitee ====

for /f "tokens=1-5 delims=/ " %%a in ('date /t') do set mydate=%%a-%%b-%%c
for /f "tokens=1-2 delims=: " %%a in ('time /t') do set mytime=%%a:%%b
set currentTime=%mydate% %mytime%

git add .
git commit -m "AI Auto Backup: %currentTime%"
git push origin main

echo ==== 备份完成！放心让 Claude 弄脏代码吧 ====
pause
