/**
 * smart_saving.js — Smart Saving & Budget Guard logic for Dompetin
 */

const SmartSaving = (() => {
    'use strict';

    const fmt = (n) => {
        const val = parseFloat(n);
        if (isNaN(val)) return 'Rp 0';
        return 'Rp ' + val.toLocaleString('id-ID');
    };
    const t = (key) => (window.i18nManager ? window.i18nManager.t(key) : key);

    let stats = null;

    // ── Fetch ────────────────────────────────────────────────────────────────

    async function fetchStats() {
        const res = await fetch('/api/smart_saving_stats');
        stats = await res.json();
        return stats;
    }

    async function fetchGoals() {
        const res = await fetch('/api/smart_goals');
        return res.json();
    }

    // ── Render: Budget Guard Banner ──────────────────────────────────────────

    function renderGuardBanner(stats) {
        const banner = document.getElementById('guard-banner');
        if (!banner || !stats.goals || stats.goals.length === 0) {
            if (banner) banner.classList.add('hidden');
            return;
        }

        const atRiskGoals = stats.goals.filter(g => g.at_risk && g.remaining_days > 0);
        if (atRiskGoals.length === 0) {
            banner.classList.add('hidden');
            return;
        }

        banner.classList.remove('hidden');
        banner.innerHTML = atRiskGoals.map(g => `
            <div class="flex items-start gap-3">
                <span class="text-2xl">⚠️</span>
                <div>
                    <p class="font-bold text-red-700 dark:text-red-300">
                        ${t('ss_target_risk').replace('{item}', g.item_name)}
                    </p>
                    <p class="text-sm text-red-600 dark:text-red-400 mt-1">
                        ${t('ss_extra_needed').replace('{amount}', fmt(g.extra_needed)).replace('{days}', g.remaining_days - 1)}
                    </p>
                </div>
            </div>
        `).join('<hr class="my-2 border-red-300"/>');
    }

    // ── Render: Today's Guard Stats ──────────────────────────────────────────

    function renderTodayStats(stats) {
        setText('stat-today-spending', fmt(stats.today_spending));
        setText('stat-today-income', fmt(stats.today_income));
        setText('stat-avg-daily', fmt(stats.avg_daily_income));

        // Per-goal "safe to spend" — use the first active goal
        const firstGoal = stats.goals && stats.goals[0];
        if (firstGoal && firstGoal.remaining_days > 0) {
            setText('stat-safe-spend', fmt(firstGoal.safe_to_spend));
            setText('stat-daily-target', fmt(firstGoal.required_daily));

            // Spending meter
            const safeSpend = firstGoal.safe_to_spend || 1;
            const pct = Math.min(100, Math.round((stats.today_spending / safeSpend) * 100));
            const bar = document.getElementById('spending-meter-bar');
            const label = document.getElementById('spending-meter-label');
            if (bar) {
                bar.style.width = pct + '%';
                bar.className = 'h-full rounded-full transition-all duration-700 ' +
                    (pct >= 100 ? 'bg-red-500' : pct >= 80 ? 'bg-amber-400' : 'bg-emerald-500');
            }
            if (label) label.textContent = pct + '%';
        } else {
            setText('stat-safe-spend', '—');
            setText('stat-daily-target', '—');
        }
    }

    // ── Render: Goal Cards ───────────────────────────────────────────────────

    function renderGoalCards(goals) {
        const container = document.getElementById('goals-container');
        const empty = document.getElementById('goals-empty');
        if (!container) return;

        if (!goals || goals.length === 0) {
            container.innerHTML = '';
            if (empty) empty.classList.remove('hidden');
            return;
        }
        if (empty) empty.classList.add('hidden');

        container.innerHTML = goals.map(g => {
            // Perbaikan Logika Tanggal & Sisa Hari
            const targetDate = new Date(g.target_date);
            const today = new Date();
            today.setHours(0, 0, 0, 0); // Reset waktu untuk perbandingan hari yang akurat
            
            // Hitung selisih hari
            const diffTime = targetDate - today;
            const remainingDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            // Gunakan nilai dari backend sebagai fallback jika perhitungan client-side gagal
            const daysLeft = isNaN(remainingDays) ? g.remaining_days : remainingDays;
            
            const isComplete = g.progress_pct >= 100;
            const isExpired = daysLeft <= 0;
            const barColor = isComplete ? 'bg-emerald-500' : isExpired ? 'bg-gray-400' : g.progress_pct >= 75 ? 'bg-blue-500' : 'bg-amber-500';

            return `
            <div class="bg-white dark:bg-slate-800 rounded-2xl shadow-lg p-6 border border-gray-100 dark:border-slate-700 transition hover:shadow-xl" data-goal-id="${g.id}">
                <div class="flex items-start justify-between mb-4">
                    <div>
                        <h3 class="text-lg font-bold text-gray-800 dark:text-white flex items-center gap-2">
                            🎯 ${g.item_name}
                            ${isComplete ? '<span class="text-xs bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300 px-2 py-0.5 rounded-full">' + t('ss_completed') + '</span>' : ''}
                            ${isExpired && !isComplete ? '<span class="text-xs bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-300 px-2 py-0.5 rounded-full">' + t('ss_expired') + '</span>' : ''}
                        </h3>
                        <p class="text-sm text-gray-500 dark:text-gray-400 mt-1">
                            📅 ${t('ss_deadline')}: ${g.target_date}
                            ${!isExpired ? ' · ' + g.remaining_days + ' ' + t('ss_days_left') : ''}
                        </p>
                    </div>
                    <button onclick="SmartSaving.deleteGoal(${g.id})" class="text-gray-400 hover:text-red-500 transition text-lg">🗑</button>
                </div>

                <!-- Progress Bar -->
                <div class="mb-3">
                    <div class="flex justify-between text-sm mb-1">
                        <span class="text-gray-600 dark:text-gray-400">${fmt(g.current_amount)} / ${fmt(g.target_amount)}</span>
                        <span class="font-semibold ${isComplete ? 'text-emerald-600' : 'text-gray-700 dark:text-gray-300'}">${g.progress_pct}%</span>
                    </div>
                    <div class="w-full bg-gray-200 dark:bg-slate-700 rounded-full h-3 overflow-hidden">
                        <div class="${barColor} h-3 rounded-full transition-all duration-700" style="width:${Math.min(100, g.progress_pct)}%"></div>
                    </div>
                </div>

                <!-- Stats Row -->
                <div class="grid grid-cols-2 gap-3 mt-4 mb-4">
                    <div class="bg-emerald-50 dark:bg-emerald-900/30 rounded-xl p-3 text-center">
                        <p class="text-xs text-emerald-600 dark:text-emerald-400 mb-1">${t('ss_daily_target')}</p>
                        <p class="text-base font-bold text-emerald-700 dark:text-emerald-300">${isComplete || isExpired ? '—' : fmt(g.required_daily)}</p>
                    </div>
                    <div class="bg-blue-50 dark:bg-blue-900/30 rounded-xl p-3 text-center">
                        <p class="text-xs text-blue-600 dark:text-blue-400 mb-1">${t('ss_days_remaining')}</p>
                        <p class="text-base font-bold text-blue-700 dark:text-blue-300">${isExpired ? 0 : daysLeft} ${t('ss_days')}</p>
                    </div>
                </div>

                <!-- Add Savings Form -->
                ${!isComplete && !isExpired ? `
                <div class="flex gap-2 mt-2">
                    <input type="number" id="add-savings-${g.id}" min="1"
                        placeholder="${t('ss_add_savings_placeholder')}"
                        class="flex-1 px-3 py-2 rounded-lg border border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-700 text-gray-800 dark:text-white text-sm focus:ring-2 focus:ring-emerald-500 focus:outline-none">
                    <button onclick="SmartSaving.addSavings(${g.id})"
                        class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2 rounded-lg text-sm font-semibold transition">
                        + ${t('ss_save')}
                    </button>
                </div>` : ''}
            </div>`;
        }).join('');
    }

    // ── Actions ──────────────────────────────────────────────────────────────

    async function addSavings(goalId) {
        const input = document.getElementById('add-savings-' + goalId);
        const amount = parseFloat(input ? input.value : 0);
        if (!amount || amount <= 0) return showToast(t('ss_enter_amount'), 'error');
        const res = await fetch(`/api/smart_goals/${goalId}`, {
            method: 'PATCH',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({add_amount: amount})
        });
        const data = await res.json();
        if (data.success) {
            showToast(t('ss_savings_added'), 'success');
            await refreshAll();
        }
    }

    async function deleteGoal(goalId) {
        if (!confirm(t('ss_delete_confirm'))) return;
        await fetch(`/api/smart_goals/${goalId}`, {method: 'DELETE'});
        showToast(t('ss_goal_deleted'), 'success');
        await refreshAll();
    }

    async function createGoal(e) {
        e.preventDefault();
        const form = document.getElementById('new-goal-form');
        const data = {
            item_name: form.item_name.value.trim(),
            target_amount: parseFloat(form.target_amount.value),
            current_amount: parseFloat(form.current_amount.value || 0),
            target_date: form.target_date.value,
            notes: form.notes ? form.notes.value : ''
        };
        if (!data.item_name || !data.target_amount || !data.target_date) {
            return showToast(t('ss_fill_required'), 'error');
        }
        const res = await fetch('/add_saving_goal', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await res.json();
        if (result.success) {
            showToast(t('ss_goal_created'), 'success');
            form.reset();
            closeModal('new-goal-modal');
            await refreshAll();
        }
    }

    // ── Helpers ──────────────────────────────────────────────────────────────

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    function showToast(msg, type = 'success') {
        if (window.NotificationManager) {
            type === 'success' ? window.NotificationManager.success(msg)
                              : window.NotificationManager.error(msg);
            return;
        }
        const toast = document.createElement('div');
        toast.className = `fixed bottom-6 right-6 z-50 px-5 py-3 rounded-xl shadow-lg text-white font-medium text-sm transition
            ${type === 'success' ? 'bg-emerald-600' : 'bg-red-500'}`;
        toast.textContent = msg;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }

    function openModal(id) {
        const m = document.getElementById(id);
        if (m) m.classList.remove('hidden');
    }

    function closeModal(id) {
        const m = document.getElementById(id);
        if (m) m.classList.add('hidden');
    }

    async function refreshAll() {
        const [s, goals] = await Promise.all([fetchStats(), fetchGoals()]);
        renderTodayStats(s);
        renderGuardBanner(s);
        renderGoalCards(goals);
    }

    // ── Init ─────────────────────────────────────────────────────────────────

    function init() {
        document.getElementById('new-goal-form')
            ?.addEventListener('submit', createGoal);

        document.getElementById('btn-new-goal')
            ?.addEventListener('click', () => openModal('new-goal-modal'));

        document.querySelectorAll('[data-close-modal]').forEach(btn => {
            btn.addEventListener('click', () => closeModal(btn.dataset.closeModal));
        });

        // Set min date to tomorrow
        const deadlineInput = document.getElementById('input-deadline');
        if (deadlineInput) {
            const tomorrow = new Date();
            tomorrow.setDate(tomorrow.getDate() + 1);
            deadlineInput.min = tomorrow.toISOString().split('T')[0];
        }

        refreshAll();
        // Auto-refresh every 60 seconds
        setInterval(refreshAll, 60000);
    }

    document.addEventListener('DOMContentLoaded', init);
    // Also listen for language changes to re-render
    document.addEventListener('languageChanged', refreshAll);

    return { addSavings, deleteGoal, openModal, closeModal, refreshAll };
})();

window.SmartSaving = SmartSaving;
