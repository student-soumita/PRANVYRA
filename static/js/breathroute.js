/**
 * PRANVYRA BreathRoute — Environmentally Aware Journey Planner
 * Feature B: Multi-Modal Journey Comparison & Exposure Risk Evaluation
 */
window.PranvyraBreathRoute = {
  currentPlan: null,

  init() {
    const form = document.getElementById('breathRouteForm');
    const useCurrentBtn = document.getElementById('routeUseCurrentOriginBtn');
    const commitBtn = document.getElementById('routeCommitTripBtn');

    if (useCurrentBtn) {
      useCurrentBtn.addEventListener('click', () => {
        const city = window.PranvyraState.profile.city;
        if (city && city !== 'null') {
          document.getElementById('routeOrigin').value = city;
        } else if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(
            (pos) => {
              document.getElementById('routeOrigin').value = `${pos.coords.latitude.toFixed(4)}, ${pos.coords.longitude.toFixed(4)}`;
            },
            () => {
              window.PranvyraAPI.showToast('Please enter your origin address or city.', 'info');
            }
          );
        }
      });
    }

    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.handlePlanSubmit();
      });
    }

    if (commitBtn) {
      commitBtn.addEventListener('click', async () => {
        await this.handleCommitTrip();
      });
    }
  },

  async handlePlanSubmit() {
    const origin = document.getElementById('routeOrigin').value.trim();
    const dest = document.getElementById('routeDestination').value.trim();
    const depTime = document.getElementById('routeDepartureTime').value;
    const manualDist = parseFloat(document.getElementById('routeManualDistance').value) || 12.0;

    if (!origin || !dest) {
      window.PranvyraAPI.showToast('Please enter both origin and destination.', 'warning');
      return;
    }

    const btn = document.querySelector('#breathRouteForm button[type="submit"]');
    if (btn) btn.disabled = true;

    try {
      const res = await window.PranvyraAPI.planBreathRoute(origin, dest, depTime, 'public_transit', manualDist);
      if (res.success && res.plan) {
        this.currentPlan = res.plan;
        this.renderPlan(res.plan);
        window.PranvyraAPI.showToast('Clean journey plan calculated successfully!', 'success');
      } else {
        window.PranvyraAPI.showToast(res.error || 'Failed to plan route.', 'error');
      }
    } catch (err) {
      console.error('BreathRoute error:', err);
    } finally {
      if (btn) btn.disabled = false;
    }
  },

  renderPlan(plan) {
    const rec = plan.recommended_mode;
    
    // Header & Rec
    const badge = document.getElementById('routeOptimalBadge');
    if (badge) {
      badge.textContent = rec.mode_name;
      badge.className = 'badge-priority high';
    }

    const titleEl = document.getElementById('routeRecTitle');
    if (titleEl) {
      titleEl.textContent = `Recommended: ${rec.mode_name} (${rec.est_minutes} mins, ${rec.emissions_kg} kg CO₂e)`;
    }

    const reasonEl = document.getElementById('routeRecReason');
    if (reasonEl) {
      reasonEl.textContent = plan.practical_recommendation || rec.exposure_advice;
    }

    // Key Stats
    const statsBox = document.getElementById('routeKeyStats');
    if (statsBox) statsBox.style.display = 'grid';

    const distEl = document.getElementById('routeStatDist');
    if (distEl) distEl.textContent = `${plan.distance_km} km`;

    const timeEl = document.getElementById('routeStatTime');
    if (timeEl) timeEl.textContent = `${rec.est_minutes} mins`;

    const savEl = document.getElementById('routeStatSavings');
    if (savEl) savEl.textContent = `${plan.savings_vs_car_kg} kg`;

    // Commit actions
    const actRow = document.getElementById('routeActionsRow');
    if (actRow) actRow.style.display = 'block';

    // Comparison Table
    const tableCard = document.getElementById('routeComparisonTableCard');
    const tbody = document.getElementById('routeModesTableBody');
    if (tableCard && tbody) {
      tableCard.style.display = 'block';
      tbody.innerHTML = '';

      plan.modes.forEach(m => {
        const tr = document.createElement('tr');
        const isRec = m.mode_key === rec.mode_key;
        if (isRec) tr.className = 'highlight-row';

        tr.innerHTML = `
          <td>
            <strong>${m.mode_name}</strong>
            ${isRec ? '<span class="status-pill active" style="margin-left: 8px;">★ Recommended</span>' : ''}
          </td>
          <td>${m.est_minutes} mins</td>
          <td>
            <span class="emission-val ${m.emissions_kg === 0 ? 'text-emerald' : ''}">${m.emissions_kg} kg</span>
          </td>
          <td>
            <div class="exp-badge ${m.exposure_level}">${m.exposure_level.toUpperCase()} EXPOSURE</div>
            <div class="exp-text">${m.exposure_advice}</div>
          </td>
        `;
        tbody.appendChild(tr);
      });
    }

    if (window.lucide) {
      window.lucide.createIcons();
    }
  },

  async handleCommitTrip() {
    if (!this.currentPlan) {
      window.PranvyraAPI.showToast('Please calculate a route first.', 'warning');
      return;
    }

    const plan = this.currentPlan;
    const origin = plan.origin.name || document.getElementById('routeOrigin').value;
    const dest = plan.destination.name || document.getElementById('routeDestination').value;
    const rec = plan.recommended_mode;

    try {
      const res = await window.PranvyraAPI.commitBreathRouteTrip(
        origin,
        dest,
        rec.mode_name,
        plan.distance_km,
        plan.savings_vs_car_kg
      );

      if (res.success && res.receipt) {
        window.PranvyraAPI.showToast(res.message, 'success');
        if (window.PranvyraState) {
          window.PranvyraState.addPoints(res.points_earned || 25);
        }
        // Open Personal Impact Receipt Modal
        if (window.PranvyraImpact && window.PranvyraImpact.openReceiptModal) {
          window.PranvyraImpact.openReceiptModal(res.receipt);
        }
      }
    } catch (err) {
      console.error('Commit trip error:', err);
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  window.PranvyraBreathRoute.init();
});

