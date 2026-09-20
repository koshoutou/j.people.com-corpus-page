#!/bin/bash

# 部署脚本用于将网站部署到Cloudflare Pages

echo "开始部署语料库网站到Cloudflare Pages..."

# 检查是否安装了wrangler
if ! command -v wrangler &> /dev/null
then
    echo "未找到wrangler命令，正在安装..."
    npm install -g wrangler
fi

# 构建项目（如果需要）
echo "构建项目..."
# 这里可以添加任何需要的构建步骤

# 部署到Cloudflare Pages
echo "部署到Cloudflare Pages..."
wrangler pages deploy . --project-name=corpus-website

echo "部署完成！"