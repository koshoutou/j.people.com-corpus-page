# 部署脚本用于将网站部署到Cloudflare Pages

Write-Host "开始部署语料库网站到Cloudflare Pages..." -ForegroundColor Green

# 检查是否安装了wrangler
$wranglerInstalled = Get-Command wrangler -ErrorAction SilentlyContinue

if (-not $wranglerInstalled) {
    Write-Host "未找到wrangler命令，正在安装..." -ForegroundColor Yellow
    npm install -g wrangler
}

# 构建项目（如果需要）
Write-Host "构建项目..." -ForegroundColor Green
# 这里可以添加任何需要的构建步骤

# 部署到Cloudflare Pages
Write-Host "部署到Cloudflare Pages..." -ForegroundColor Green
wrangler pages deploy . --project-name=corpus-website

Write-Host "部署完成！" -ForegroundColor Green