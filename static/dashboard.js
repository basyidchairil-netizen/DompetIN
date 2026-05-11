// dashboard.js — Live data rendering for Dompetin Dashboard

const fmt = (n) => 'Rp ' + Number(n || 0).toLocaleString('id-ID');
const t = (key) => window.i18nManager ? window.i18nManager.t(key) : key;

let spendingChart = null;

// ── Fetch & Render Summary ────────────────────────────────────────────────────
async function loadSummary() {
    try {
        const res = await fetch('/api/summary');
        const d = await res.json();

        // Stat cards
        setText('dash-balance',   fmt(d.balance));
        setText('dash-income',    fmt(d.monthly_income));
        setText('dash-expense',   fmt(d.monthly_expense));
        setText('dash-savings',   fmt(d.monthly_savings));
        setText('dash-save-rate', (d.saving_rate || 0) + '%');

        // Saving rate bar
        const ratePct = Math.min(100, Math.max(0, d.saving_rate || 0));
        const rateBar = document.getElementById('dash-rate-bar');
        if (rateBar) {
            rateBar.style.width = ratePct + '%';
            rateBar.className = 'h-2 rounded-full transition-all duration-700 ' +
                (ratePct >= 20 ? 'bg-emerald-500' : ratePct >= 10 ? 'bg-amber-400' : 'bg-red-400');
        }

        // Chart
        renderSpendingChart(d.spending_by_category);

        // Recent transactions
        renderRecentTransactions(d.recent_transactions);

    } catch (e) {
        console.error('Summary fetch error', e);
    }
}

// ── Spending Chart ────────────────────────────────────────────────────────────
function renderSpendingChart(data) {
    const canvas = document.getElementById('spending-chart');
    if (!canvas || !window.Chart) return;

    const labels = data.map(d => d.category);
    const values = data.map(d => d.amount);
    const colors = [
        '#10b981','#3b82f6','#f59e0b','#ef4444','#8b5cf6',
        '#06b6d4','#f97316','#84cc16','#ec4899','#6366f1'
    ];

    if (spendingChart) spendingChart.destroy();

    spendingChart = new Chart(canvas, {
        type: 'bar',
        data: {
            labels: labels.length ? labels : [t('income_no_expenses')],
            datasets: [{
                label: t('dashboard_monthly_expenses'),
                data: values.length ? values : [0],
                backgroundColor: colors.slice(0, Math.max(labels.length, 1)),
                borderRadius: 8,
                borderSkipped: false,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label: (ctx) => ' ' + fmt(ctx.raw)
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: (v) => 'Rp ' + Number(v).toLocaleString('id-ID'),
                        color: document.documentElement.classList.contains('dark') ? '#94a3b8' : '#6b7280',
                    },
                    grid: { color: document.documentElement.classList.contains('dark') ? '#334155' : '#f1f5f9' }
                },
                x: {
                    ticks: { color: document.documentElement.classList.contains('dark') ? '#94a3b8' : '#6b7280' },
                    grid: { display: false }
                }
            }
        }
    });
}

// ── Recent Transactions ───────────────────────────────────────────────────────
function renderRecentTransactions(txns) {
    const container = document.getElementById('recent-txn-list');
    if (!container) return;

    if (!txns || txns.length === 0) {
        container.innerHTML = `<p class="text-center text-gray-400 py-4">${t('income_no_transactions')}</p>`;
        return;
    }

    container.innerHTML = txns.map(tx => `
        <div class="flex items-center justify-between py-3 border-b border-gray-100 dark:border-slate-700 last:border-0">
            <div class="flex items-center gap-3">
                <div class="w-9 h-9 rounded-full flex items-center justify-center ${tx.type === 'income' ? 'bg-emerald-100 dark:bg-emerald-900/40' : 'bg-red-100 dark:bg-red-900/40'}">
                    <i class="fas ${tx.type === 'income' ? 'fa-arrow-down text-emerald-600' : 'fa-arrow-up text-red-500'} text-sm"></i>
                </div>
                <div>
                    <p class="text-sm font-medium text-gray-800 dark:text-white">${tx.desc || tx.category}</p>
                    <p class="text-xs text-gray-400">${tx.date} · ${tx.category}</p>
                </div>
            </div>
            <p class="font-semibold text-sm ${tx.type === 'income' ? 'text-emerald-600' : 'text-red-500'}">
                ${tx.type === 'income' ? '+' : '-'}${fmt(tx.amount)}
            </p>
        </div>
    `).join('');
}

// ── Add Transaction ───────────────────────────────────────────────────────────
function openModal() {
    document.getElementById('transaction-modal').classList.remove('hidden');
    // Set today's date as default
    const dateInput = document.querySelector('#transaction-form [name="date"]');
    if (dateInput && !dateInput.value) {
        dateInput.value = new Date().toISOString().split('T')[0];
    }
}

function closeModal() {
    document.getElementById('transaction-modal').classList.add('hidden');
}

document.addEventListener('DOMContentLoaded', function () {
    // Form submit
    const form = document.getElementById('transaction-form');
    if (form) {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            const data = Object.fromEntries(new FormData(this));
            data.amount = parseFloat(data.amount);
            try {
                const res = await fetch('/add_transaction', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data),
                });
                const result = await res.json();
                if (result.success) {
                    closeModal();
                    form.reset();
                    if (result.nudge && window.NotificationManager) {
                        window.NotificationManager.warning(result.nudge);
                    }
                    // Refresh all stats live
                    await loadSummary();
                }
            } catch (err) {
                console.error('Add transaction error', err);
            }
        });
    }

    // Initial load
    loadSummary();

    // Re-render on language change (chart labels)
    document.addEventListener('languageChanged', loadSummary);

    // Sidebar toggle
    window.toggleSidebar = function () {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');
        if (sidebar.classList.contains('-translate-x-full')) {
            sidebar.classList.remove('-translate-x-full');
            overlay.classList.remove('hidden');
        } else {
            sidebar.classList.add('-translate-x-full');
            overlay.classList.add('hidden');
        }
    };
});

function setText(id, value) {
    const el = document.getElementById(id);
    if (el) el.textContent = value;
}
