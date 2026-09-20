/**
 * 人民网中日对译语料库 - 前端逻辑
 * 单次加载 corpus.json，内存搜索，XSS 安全
 */

// --- 全局状态 ---
let allData = [];        // 完整语料
let filteredData = [];   // 当前筛选结果
let currentPage = 1;
let itemsPerPage = 10;
let totalPages = 1;
let searchTerm = '';
let stats = { total: 0, sources: 0, titles: 0 };

// --- HTML 转义（防 XSS）---
function esc(str) {
    if (!str) return '';
    var d = document.createElement('div');
    d.textContent = str;
    return d.innerHTML;
}

// --- 高亮关键词（安全）---
function highlight(text, term) {
    if (!term) return esc(text);
    var safe = esc(text);
    var escaped = term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    return safe.replace(new RegExp('(' + escaped + ')', 'gi'), '<span class="highlight">$1</span>');
}

// --- 初始化 ---
document.addEventListener('DOMContentLoaded', function() {
    loadStats();
    loadCorpus();
    setupEvents();
});

// --- 加载统计 ---
async function loadStats() {
    try {
        var r = await fetch('data/pages/stats.json');
        if (r.ok) {
            stats = await r.json();
            document.getElementById('total-sentences').textContent = (stats.total_sentences || 0).toLocaleString();
            document.getElementById('unique-sources').textContent = (stats.unique_sources || 0).toLocaleString();
            document.getElementById('unique-titles').textContent = (stats.unique_titles || 0).toLocaleString();
        }
    } catch (e) {
        console.warn('统计加载失败', e);
    }
}

// --- 加载完整语料（单次请求）---
async function loadCorpus() {
    try {
        var r = await fetch('data/corpus.json');
        if (!r.ok) throw new Error('HTTP ' + r.status);
        allData = await r.json();
        filteredData = allData;
        totalPages = Math.ceil(allData.length / itemsPerPage);
        currentPage = 1;
        renderPage();
        renderPagination();
        console.log('语料加载完成: ' + allData.length + ' 条');
    } catch (e) {
        console.error('语料加载失败', e);
        document.getElementById('sentence-list').innerHTML =
            '<div class="no-results"><p>数据加载失败，请稍后重试</p></div>';
    }
}

// --- 搜索 ---
function doSearch(term) {
    searchTerm = term.trim();
    if (!searchTerm) {
        filteredData = allData;
    } else {
        filteredData = allData.filter(function(item) {
            return (item.zh && item.zh.includes(searchTerm)) ||
                   (item.ja && item.ja.includes(searchTerm)) ||
                   (item.title && item.title.includes(searchTerm));
        });
    }
    totalPages = Math.max(1, Math.ceil(filteredData.length / itemsPerPage));
    currentPage = 1;
    renderPage();
    renderPagination();
    updateSearchStats();
}

// --- 搜索时更新统计显示 ---
function updateSearchStats() {
    if (searchTerm) {
        document.getElementById('total-sentences').textContent = filteredData.length.toLocaleString();
        document.getElementById('unique-sources').textContent =
            new Set(filteredData.map(function(i) { return i.source_url; })).size.toLocaleString();
        document.getElementById('unique-titles').textContent =
            new Set(filteredData.map(function(i) { return i.title; })).size.toLocaleString();
    } else {
        document.getElementById('total-sentences').textContent = (stats.total_sentences || allData.length).toLocaleString();
        document.getElementById('unique-sources').textContent = (stats.unique_sources || 0).toLocaleString();
        document.getElementById('unique-titles').textContent = (stats.unique_titles || 0).toLocaleString();
    }
}

// --- 渲染当前页 ---
function renderPage() {
    var list = document.getElementById('sentence-list');
    var start = (currentPage - 1) * itemsPerPage;
    var end = Math.min(start + itemsPerPage, filteredData.length);
    var items = filteredData.slice(start, end);

    if (items.length === 0) {
        list.innerHTML = '<div class="no-results"><p>' +
            (searchTerm ? '没有找到匹配的语句' : '暂无数据') + '</p></div>';
        return;
    }

    var html = [];
    for (var i = 0; i < items.length; i++) {
        var item = items[i];
        var zh = highlight(item.zh, searchTerm);
        var ja = highlight(item.ja, searchTerm);
        var title = highlight(item.title, searchTerm);
        var url = esc(item.source_url);

        html.push(
            '<div class="sentence-item" style="animation-delay:' + (i * 0.05) + 's">' +
                '<div class="sentence-chinese">' + zh + '</div>' +
                '<div class="sentence-japanese">' + ja + '</div>' +
                '<div class="source">来源: <a href="' + url + '" target="_blank" rel="noopener">' + title + '</a></div>' +
            '</div>'
        );
    }
    list.innerHTML = html.join('');
}

// --- 渲染分页控件 ---
function renderPagination() {
    document.getElementById('current-page-num').textContent = currentPage;
    document.getElementById('total-pages-num').textContent = totalPages;
    document.getElementById('prev-page').disabled = currentPage <= 1;
    document.getElementById('next-page').disabled = currentPage >= totalPages;
}

// --- 翻页 ---
function goToPage(page) {
    if (page < 1) page = 1;
    if (page > totalPages) page = totalPages;
    if (page === currentPage) return;
    currentPage = page;
    renderPage();
    renderPagination();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// --- 事件绑定 ---
function setupEvents() {
    var input = document.getElementById('search-input');
    var btn = document.getElementById('search-button');

    btn.addEventListener('click', function() { doSearch(input.value); });

    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') doSearch(input.value);
    });

    var debounce;
    input.addEventListener('input', function() {
        clearTimeout(debounce);
        debounce = setTimeout(function() { doSearch(input.value); }, 300);
    });

    document.getElementById('prev-page').addEventListener('click', function() { goToPage(currentPage - 1); });
    document.getElementById('next-page').addEventListener('click', function() { goToPage(currentPage + 1); });
}
