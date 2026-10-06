let state = {
    page: 1,
    pageSize: 15,
    totalPages: 1,
    totalRecords: 0,
    source: "all",
    rating: "all",
    search: "",
    isScraping: false,
    cachedItems: [],
};

const searchInput = document.getElementById("search-input");
const clearSearchBtn = document.getElementById("clear-search");
const ratingFilter = document.getElementById("rating-filter");
const pageSizeSelect = document.getElementById("pagesize-select");
const tableBody = document.getElementById("table-body");
const prevPageBtn = document.getElementById("prev-page-btn");
const nextPageBtn = document.getElementById("next-page-btn");
const pageIndicator = document.getElementById("page-indicator");
const paginationSummary = document.getElementById("pagination-summary");
const runScraperBtn = document.getElementById("run-scraper-btn");
const progressBanner = document.getElementById("progress-banner");
const progressStepText = document.getElementById("progress-step-text");
const progressDescText = document.getElementById("progress-desc-text");
const progressBarFill = document.getElementById("progress-bar-fill");
const progressPctBadge = document.getElementById("progress-pct-badge");
const sourceSegmented = document.getElementById("source-segmented");

const statTotalRecords = document.getElementById("stat-total-records");
const statBooksCount = document.getElementById("stat-books-count");
const statQuotesCount = document.getElementById("stat-quotes-count");
const statDuplicatesCount = document.getElementById("stat-duplicates-count");
const statDuration = document.getElementById("stat-duration");
const countAll = document.getElementById("count-all");
const countBooks = document.getElementById("count-books");
const countQuotes = document.getElementById("count-quotes");
const ratioBooksBar = document.getElementById("ratio-books-bar");
const ratioQuotesBar = document.getElementById("ratio-quotes-bar");
const statusLabel = document.getElementById("status-label");
const mongoLabel = document.getElementById("mongo-label");

const recordModal = document.getElementById("record-modal");
const modalClose = document.getElementById("modal-close");
const modalTitle = document.getElementById("modal-title");
const modalBadge = document.getElementById("modal-badge");
const modalBody = document.getElementById("modal-body");
const modalOpenLink = document.getElementById("modal-open-link");
const toastContainer = document.getElementById("toast-container");

async function fetchStats() {
    try {
        const res = await fetch("/api/stats");
        if (!res.ok) return;
        const data = await res.json();

        statTotalRecords.textContent = Number(data.total_records).toLocaleString();
        statBooksCount.textContent = Number(data.books_count).toLocaleString();
        statQuotesCount.textContent = Number(data.quotes_count).toLocaleString();

        countAll.textContent = Number(data.total_records).toLocaleString();
        countBooks.textContent = Number(data.books_count).toLocaleString();
        countQuotes.textContent = Number(data.quotes_count).toLocaleString();

        const total = data.total_records || 1;
        const booksPct = ((data.books_count / total) * 100).toFixed(1);
        const quotesPct = ((data.quotes_count / total) * 100).toFixed(1);

        if (ratioBooksBar) ratioBooksBar.style.width = `${booksPct}%`;
        if (ratioQuotesBar) ratioQuotesBar.style.width = `${quotesPct}%`;

        if (data.report) {
            statDuplicatesCount.textContent = data.report.deduplication?.duplicates_detected ?? 0;
            statDuration.textContent = `${data.report.duration_seconds}s`;
        }

        updatePipelineStatus(data.pipeline_state);
    } catch (err) {
        console.error("Error fetching stats:", err);
    }
}

async function fetchMongoStatus() {
    try {
        const res = await fetch("/api/mongodb/status");
        if (!res.ok) return;
        const data = await res.json();

        if (mongoLabel) {
            if (data.connected) {
                mongoLabel.textContent = `MongoDB (${data.database})`;
                mongoLabel.style.color = "#34d399";
            } else {
                mongoLabel.textContent = "CSV Mode (Offline)";
                mongoLabel.style.color = "#fbbf24";
            }
        }
    } catch (err) {
        console.error("Error checking MongoDB:", err);
    }
}

async function fetchData() {
    tableBody.innerHTML = `
        <tr>
            <td colspan="7" class="empty-state-cell" style="text-align: center; padding: 60px 20px;">
                <div class="table-loader" style="display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; margin: 0 auto; width: 100%; gap: 12px;">
                    <div class="progress-spinner-ring" style="width: 28px; height: 28px; border-width: 3px; margin: 0 auto;"></div>
                    <span>Retrieving dataset records...</span>
                </div>
            </td>
        </tr>
    `;

    const params = new URLSearchParams({
        page: state.page,
        page_size: state.pageSize,
    });

    if (state.source && state.source !== "all") {
        params.append("source", state.source);
    }
    if (state.rating && state.rating !== "all") {
        params.append("rating", state.rating);
    }
    if (state.search) {
        params.append("search", state.search);
    }

    try {
        const res = await fetch(`/api/data?${params.toString()}`);
        if (!res.ok) throw new Error("Failed to load records");
        const data = await res.json();

        state.totalRecords = data.total;
        state.totalPages = data.total_pages;
        state.cachedItems = data.items || [];

        renderTable(data.items);
        renderPagination();
    } catch (err) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="empty-state-cell" style="color: #f43f5e; text-align: center; padding: 60px 20px;">
                    Failed to load data. Run the scraper pipeline first.
                </td>
            </tr>
        `;
    }
}

function renderTable(items) {
    if (!items || items.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="empty-state-cell" style="padding: 48px; text-align: center; color: var(--text-muted);">
                    <div style="font-size: 24px; margin-bottom: 8px;">🔍</div>
                    <div style="font-size: 15px; font-weight: 600; color: #ffffff;">No matching records found</div>
                    <div style="font-size: 13px;">Try clearing filters or running a new search query.</div>
                </td>
            </tr>
        `;
        return;
    }

    const rowsHtml = items.map((item, index) => {
        const isBook = item.source === "Books to Scrape";
        const badgeClass = isBook ? "source-books" : "source-quotes";
        const badgeIcon = isBook ? "📚" : "💬";

        const priceDisplay = item.price !== null && item.price !== undefined
            ? `<span class="price-pill">£${Number(item.price).toFixed(2)}</span>`
            : `<span class="null-text">—</span>`;

        let ratingDisplay = `<span class="null-text">—</span>`;
        if (item.rating) {
            const stars = "★".repeat(item.rating) + "☆".repeat(5 - item.rating);
            ratingDisplay = `<span class="stars-rating" title="${item.rating} out of 5 stars">${stars}</span>`;
        }

        let authorOrInfo = `<span class="null-text">—</span>`;
        if (item.author) {
            authorOrInfo = `<div class="record-author-cell"><span class="author-icon">👤</span> ${escapeHtml(item.author)}</div>`;
        } else if (item.category) {
            authorOrInfo = `<div class="record-author-cell"><span class="author-icon">📂</span> ${escapeHtml(item.category)}</div>`;
        } else if (isBook) {
            authorOrInfo = `<div class="record-author-cell"><span class="author-icon">📚</span> Books / Catalogue</div>`;
        }

        let tagsDisplay = `<span class="null-text">—</span>`;
        if (item.tags) {
            const tagList = item.tags.split(";");
            tagsDisplay = `
                <div class="tags-cell">
                    ${tagList.slice(0, 3).map(t => `<span class="tag-badge" onclick="event.stopPropagation(); filterByTag('${escapeHtml(t)}')">#${escapeHtml(t)}</span>`).join("")}
                    ${tagList.length > 3 ? `<span class="tag-badge" style="opacity: 0.6;">+${tagList.length - 3}</span>` : ""}
                </div>
            `;
        } else if (isBook) {
            tagsDisplay = `
                <div class="tags-cell">
                    <span class="tag-badge" onclick="event.stopPropagation(); filterByTag('books')">#books</span>
                    <span class="tag-badge" onclick="event.stopPropagation(); filterByTag('catalogue')">#catalogue</span>
                </div>
            `;
        }

        const linkDisplay = item.source_url
            ? `<a href="${item.source_url}" target="_blank" rel="noopener noreferrer" class="action-icon-link" onclick="event.stopPropagation();" title="View Source">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
                    <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                    <polyline points="15 3 21 3 21 9"></polyline>
                    <line x1="10" y1="14" x2="21" y2="3"></line>
                </svg>
               </a>`
            : `<span class="null-text">—</span>`;

        return `
            <tr onclick="openRecordModal(${index})">
                <td>
                    <span class="source-badge ${badgeClass}">${badgeIcon} ${escapeHtml(item.source)}</span>
                </td>
                <td>
                    <div class="table-title-cell">
                        <span class="${isBook ? 'record-title' : 'record-quote'}">${escapeHtml(item.name_or_title || "Untitled")}</span>
                    </div>
                </td>
                <td>${authorOrInfo}</td>
                <td>${priceDisplay}</td>
                <td>${ratingDisplay}</td>
                <td>${tagsDisplay}</td>
                <td style="text-align: center;">${linkDisplay}</td>
            </tr>
        `;
    }).join("");

    tableBody.innerHTML = rowsHtml;
}

function renderPagination() {
    const start = state.totalRecords === 0 ? 0 : (state.page - 1) * state.pageSize + 1;
    const end = Math.min(state.page * state.pageSize, state.totalRecords);

    paginationSummary.innerHTML = `Showing <strong>${start.toLocaleString()}</strong> to <strong>${end.toLocaleString()}</strong> of <strong>${state.totalRecords.toLocaleString()}</strong> records`;
    pageIndicator.textContent = `Page ${state.page} of ${state.totalPages}`;

    prevPageBtn.disabled = state.page <= 1;
    nextPageBtn.disabled = state.page >= state.totalPages;
}

function openRecordModal(index) {
    const item = state.cachedItems[index];
    if (!item) return;

    modalTitle.textContent = item.name_or_title || "Record Details";
    const isBook = item.source === "Books to Scrape";
    modalBadge.className = `badge ${isBook ? 'source-books' : 'source-quotes'}`;
    modalBadge.textContent = item.source;

    let bodyHtml = `
        <div class="modal-kv-row">
            <span class="modal-kv-label">Title / Quote</span>
            <div class="modal-kv-value" style="font-weight: 600;">${escapeHtml(item.name_or_title)}</div>
        </div>
    `;

    let authorVal = item.author
        ? `👤 ${escapeHtml(item.author)}`
        : (item.category ? `📂 ${escapeHtml(item.category)}` : (isBook ? `📚 Books / Catalogue` : null));
    if (authorVal) {
        bodyHtml += `
            <div class="modal-kv-row">
                <span class="modal-kv-label">Author / Meta</span>
                <div class="modal-kv-value">${authorVal}</div>
            </div>
        `;
    }

    if (item.price !== null && item.price !== undefined) {
        bodyHtml += `
            <div class="modal-kv-row">
                <span class="modal-kv-label">Price</span>
                <div class="modal-kv-value" style="color: #38bdf8; font-weight: 700;">£${Number(item.price).toFixed(2)}</div>
            </div>
        `;
    }

    if (item.rating) {
        bodyHtml += `
            <div class="modal-kv-row">
                <span class="modal-kv-label">Rating</span>
                <div class="modal-kv-value" style="color: #f59e0b;">${"★".repeat(item.rating)}${"☆".repeat(5 - item.rating)} (${item.rating} / 5)</div>
            </div>
        `;
    }

    let tagsList = item.tags ? item.tags.split(";") : (isBook ? ["books", "catalogue"] : []);
    if (tagsList.length > 0) {
        bodyHtml += `
            <div class="modal-kv-row">
                <span class="modal-kv-label">Tags</span>
                <div class="modal-kv-value" style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px;">
                    ${tagsList.map(t => `<span class="tag-badge">#${escapeHtml(t)}</span>`).join("")}
                </div>
            </div>
        `;
    }

    if (item.scraped_at) {
        bodyHtml += `
            <div class="modal-kv-row">
                <span class="modal-kv-label">Scraped Timestamp</span>
                <div class="modal-kv-value" style="font-family: var(--font-mono); font-size: 12.5px; color: var(--text-muted);">${escapeHtml(item.scraped_at)}</div>
            </div>
        `;
    }

    modalBody.innerHTML = bodyHtml;
    if (item.source_url) {
        modalOpenLink.href = item.source_url;
        modalOpenLink.classList.remove("hidden");
    } else {
        modalOpenLink.classList.add("hidden");
    }

    recordModal.classList.remove("hidden");
}

function closeModal() {
    recordModal.classList.add("hidden");
}

function updatePipelineStatus(pipeline) {
    if (!pipeline) return;

    if (pipeline.is_running) {
        if (statusLabel) statusLabel.textContent = "Pipeline Scraping...";
        runScraperBtn.disabled = true;
        progressBanner.classList.remove("hidden");
        progressStepText.textContent = pipeline.current_step;
        progressBarFill.style.width = `${pipeline.progress_percent}%`;
        if (progressPctBadge) progressPctBadge.textContent = `${pipeline.progress_percent}%`;
    } else {
        runScraperBtn.disabled = false;
        progressBanner.classList.add("hidden");
        if (statusLabel) {
            statusLabel.textContent = pipeline.status === "completed" ? "Pipeline Completed" : "Pipeline Ready";
        }
    }
}

async function runPipeline() {
    if (confirm("Run the ETL Scraping Pipeline now across Books and Quotes?")) {
        try {
            runScraperBtn.disabled = true;
            showToast("🚀 Initiating ETL scraping pipeline...");
            const res = await fetch("/api/scrape", { method: "POST" });
            if (res.ok) {
                pollStatus();
            } else {
                showToast("⚠️ Pipeline already running.");
                runScraperBtn.disabled = false;
            }
        } catch (err) {
            console.error("Error triggering scraper:", err);
            runScraperBtn.disabled = false;
        }
    }
}

function pollStatus() {
    const interval = setInterval(async () => {
        try {
            const res = await fetch("/api/scrape/status");
            if (res.ok) {
                const status = await res.json();
                updatePipelineStatus(status);
                if (!status.is_running) {
                    clearInterval(interval);
                    showToast("✅ Pipeline finished successfully!");
                    fetchStats();
                    fetchData();
                }
            }
        } catch (err) {
            clearInterval(interval);
        }
    }, 2000);
}

function showToast(message) {
    const toast = document.createElement("div");
    toast.className = "toast";
    toast.innerHTML = `<span>${message}</span>`;
    toastContainer.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(40px)";
        setTimeout(() => toast.remove(), 300);
    }, 3200);
}

function filterByTag(tag) {
    searchInput.value = tag;
    clearSearchBtn.classList.remove("hidden");
    state.search = tag;
    state.page = 1;
    fetchData();
    showToast(`Filtered by tag: #${tag}`);
}

function escapeHtml(text) {
    if (!text) return "";
    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

let searchDebounce = null;
searchInput.addEventListener("input", (e) => {
    const val = e.target.value;
    clearSearchBtn.classList.toggle("hidden", !val);
    clearTimeout(searchDebounce);
    searchDebounce = setTimeout(() => {
        state.search = val;
        state.page = 1;
        fetchData();
    }, 280);
});

clearSearchBtn.addEventListener("click", () => {
    searchInput.value = "";
    clearSearchBtn.classList.add("hidden");
    state.search = "";
    state.page = 1;
    fetchData();
});

if (sourceSegmented) {
    sourceSegmented.querySelectorAll(".segment-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            sourceSegmented.querySelectorAll(".segment-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            state.source = btn.getAttribute("data-source");
            state.page = 1;
            fetchData();
        });
    });
}

ratingFilter.addEventListener("change", (e) => {
    state.rating = e.target.value;
    state.page = 1;
    fetchData();
});

pageSizeSelect.addEventListener("change", (e) => {
    state.pageSize = parseInt(e.target.value, 10);
    state.page = 1;
    fetchData();
});

prevPageBtn.addEventListener("click", () => {
    if (state.page > 1) {
        state.page -= 1;
        fetchData();
    }
});

nextPageBtn.addEventListener("click", () => {
    if (state.page < state.totalPages) {
        state.page += 1;
        fetchData();
    }
});

runScraperBtn.addEventListener("click", runPipeline);

if (modalClose) modalClose.addEventListener("click", closeModal);
if (recordModal) {
    recordModal.addEventListener("click", (e) => {
        if (e.target === recordModal) closeModal();
    });
}

document.addEventListener("keydown", (e) => {
    if (e.key === "/" && document.activeElement !== searchInput) {
        e.preventDefault();
        searchInput.focus();
    }
    if (e.key === "Escape" && !recordModal.classList.contains("hidden")) {
        closeModal();
    }
});

document.addEventListener("DOMContentLoaded", () => {
    fetchStats();
    fetchMongoStatus();
    fetchData();
});
