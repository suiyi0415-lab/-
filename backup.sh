#!/bin/bash
# 自动备份脚本 - 备份到 Gitee
# 使用方式: ./backup.sh
# Windows 用户可用 Git Bash 运行

echo "==== 开始自动备份到 Gitee ===="

# 获取当前时间作为提交信息
currentTime=$(date "+%Y-%m-%d %H:%M:%S")

git add .
git commit -m "AI Auto Backup: $currentTime"
git push origin main

echo "==== 备份完成！放心让 Claude 弄脏代码吧 ===="
