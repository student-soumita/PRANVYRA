/**
 * PRANVYRA Daily Routine Planner Controller
 * Open-Access: Uses visitor_id via API layer, no demo account references.
 */
window.PranvyraPlanner = {
  tasks: [],

  init() {
    this.bindEvents();
    this.loadTodayPlanner();
  },

  bindEvents() {
    const regenBtn = document.getElementById('plannerRegenerateBtn');
    if (regenBtn) {
      regenBtn.addEventListener('click', async () => {
        try {
          const res = await window.PranvyraAPI.regeneratePlanner();
          if (res.success) {
            this.tasks = res.tasks;
            this.renderTasks();
            this.updateProgress(res.completion_percentage, res.completed_tasks, res.total_tasks);
            window.PranvyraAPI.showToast('Daily routine calibrated to latest atmospheric data.', 'success');
          }
        } catch (e) {
          window.PranvyraAPI.showToast('Could not regenerate planner.', 'error');
        }
      });
    }
  },

  async loadTodayPlanner() {
    try {
      const res = await window.PranvyraAPI.getDailyPlanner();
      if (res.success) {
        this.tasks = res.tasks;
        this.renderTasks();
        this.updateProgress(res.completion_percentage, res.completed_tasks, res.total_tasks);
      }
    } catch (e) {
      console.warn("Could not load planner:", e);
    }
  },

  renderTasks() {
    const slots = {
      morning: document.getElementById('slotMorningTasks'),
      afternoon: document.getElementById('slotAfternoonTasks'),
      evening: document.getElementById('slotEveningTasks')
    };

    Object.values(slots).forEach(el => {
      if (el) el.innerHTML = '';
    });

    this.tasks.forEach(task => {
      const targetCol = slots[task.time_slot] || slots.morning;
      if (!targetCol) return;

      const item = document.createElement('div');
      item.className = `planner-task-item ${task.is_completed ? 'completed' : ''}`;
      item.setAttribute('data-task-id', task.id);

      item.innerHTML = `
        <div class="task-checkbox">
          <i data-lucide="check"></i>
        </div>
        <div class="task-content">
          <div class="task-top">
            <span class="task-title">${this.escapeHtml(task.title)}</span>
            <span class="badge-priority ${task.priority}">${task.priority}</span>
          </div>
          <p class="task-desc">${this.escapeHtml(task.description)}</p>
        </div>
      `;

      item.addEventListener('click', () => this.toggleTask(task.id));
      targetCol.appendChild(item);
    });

    if (window.lucide) {
      window.lucide.createIcons();
    }
  },

  async toggleTask(taskId) {
    try {
      const res = await window.PranvyraAPI.togglePlannerTask(taskId);
      if (res.success) {
        const task = this.tasks.find(t => t.id === taskId);
        if (task) {
          task.is_completed = res.is_completed ? 1 : 0;
        }
        this.renderTasks();
        const completedCount = this.tasks.filter(t => t.is_completed).length;
        this.updateProgress(res.completion_percentage, completedCount, this.tasks.length);
        
        if (res.points_delta > 0) {
          window.PranvyraState.addPoints(res.points_delta);
          window.PranvyraAPI.showToast(`Action completed! +${res.points_delta} Green Points earned.`, 'success');
        }
      }
    } catch (e) {
      window.PranvyraAPI.showToast('Could not update task status.', 'warning');
    }
  },

  updateProgress(pct, completed, total) {
    const pctEl = document.getElementById('plannerCompletionPct');
    const barEl = document.getElementById('plannerProgressBar');
    const countEl = document.getElementById('plannerTaskCount');

    if (pctEl) pctEl.textContent = `${pct}%`;
    if (barEl) barEl.style.width = `${pct}%`;
    if (countEl) countEl.textContent = `${completed} of ${total} actions completed today`;
  },

  escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
};
