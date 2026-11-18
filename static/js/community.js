/**
 * PRANVYRA Neighborhood Pulse — Community Environmental Intelligence
 * Feature D: Real Collective Ledger with ZERO fabricated stats
 */
window.PranvyraCommunity = {
  init() {
    this.loadPulse();
    this.loadChallenges();
  },

  async loadPulse() {
    try {
      const res = await window.PranvyraAPI.getNeighborhoodPulse();
      if (res.success && res.pulse) {
        const p = res.pulse;
        const actEl = document.getElementById('pulseTotalActions');
        const co2El = document.getElementById('pulseTotalCo2');
        const citEl = document.getElementById('pulseActiveCitizens');
        const compEl = document.getElementById('pulseCompletedChallenges');

        if (actEl) actEl.textContent = p.total_actions_logged;
        if (co2El) co2El.textContent = `${p.total_co2_avoided_kg} kg`;
        if (citEl) citEl.textContent = p.active_citizens_count;
        if (compEl) compEl.textContent = p.completed_challenges_count;
      }
    } catch (e) {
      console.warn("Could not load neighborhood pulse:", e);
    }
  },

  async loadChallenges() {
    try {
      const res = await window.PranvyraAPI.getCommunityChallenges();
      if (res.success && res.challenges) {
        const grid = document.getElementById('communityChallengesGrid');
        if (!grid) return;

        grid.innerHTML = '';
        res.challenges.forEach(c => {
          const card = document.createElement('div');
          card.className = 'challenge-card glass-card';

          const isJoined = c.user_status !== 'not_joined';
          const isDone = c.user_status === 'completed';

          let actionBtnHtml = '';
          if (!isJoined) {
            actionBtnHtml = `<button class="btn btn-primary btn-sm join-btn">Join Challenge</button>`;
          } else if (!isDone) {
            actionBtnHtml = `<button class="btn btn-outline btn-sm progress-btn"><i data-lucide="plus"></i> Log Step (+35%)</button>`;
          } else {
            actionBtnHtml = `<span class="badge-priority high"><i data-lucide="check"></i> Completed</span>`;
          }

          card.innerHTML = `
            <div>
              <div class="challenge-top">
                <span class="card-eyebrow">${c.category.toUpperCase()}</span>
                <span class="challenge-points">+${c.points} pts</span>
              </div>
              <h4 class="challenge-title">${this.escapeHtml(c.title)}</h4>
              <p class="challenge-desc">${this.escapeHtml(c.description)}</p>
            </div>
            
            <div>
              <div class="challenge-progress-bar">
                <div class="challenge-fill" style="width: ${c.user_progress}%;"></div>
              </div>
              <div class="challenge-meta-row">
                <span>Progress: <strong>${c.user_progress}%</strong></span>
                <span>${c.participants_count} Citizens Active</span>
              </div>
              <div class="challenge-actions">
                ${actionBtnHtml}
              </div>
            </div>
          `;

          // Bind Join
          const joinBtn = card.querySelector('.join-btn');
          if (joinBtn) {
            joinBtn.addEventListener('click', async () => {
              const jRes = await window.PranvyraAPI.joinChallenge(c.id);
              if (jRes.success) {
                window.PranvyraAPI.showToast(jRes.message, 'success');
                this.loadChallenges();
                this.loadPulse();
              }
            });
          }

          // Bind Progress
          const progBtn = card.querySelector('.progress-btn');
          if (progBtn) {
            progBtn.addEventListener('click', async () => {
              const pRes = await window.PranvyraAPI.updateChallengeProgress(c.id, 35);
              if (pRes.success) {
                if (pRes.status === 'completed') {
                  window.PranvyraState.addPoints(c.points);
                  window.PranvyraAPI.showToast(`Challenge Completed! Unlocked badge '${pRes.badge_awarded}' and earned +${c.points} pts!`, 'success');
                } else {
                  window.PranvyraAPI.showToast(`Logged milestone for '${c.title}'! Progress now ${pRes.progress_pct}%.`, 'info');
                }
                this.loadChallenges();
                this.loadPulse();
              }
            });
          }

          grid.appendChild(card);
        });

        if (window.lucide) {
          window.lucide.createIcons();
        }
      }
    } catch (e) {
      console.warn("Could not load community challenges:", e);
    }
  },

  escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }
};
