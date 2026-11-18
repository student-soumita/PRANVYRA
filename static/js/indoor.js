/**
 * PRANVYRA Indoor Air Intelligence Controller
 * Open-Access: Uses visitor_id via API layer.
 */
window.PranvyraIndoor = {
  init() {
    this.bindEvents();
    this.loadLatestCheck();
  },

  bindEvents() {
    const form = document.getElementById('indoorAuditForm');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const payload = {
          room_size: document.getElementById('indoorRoomSize').value,
          occupants: parseInt(document.getElementById('indoorOccupants').value) || 2,
          ventilation: document.getElementById('indoorVentilation').value,
          cooking_fuel: document.getElementById('indoorCookingFuel').value,
          dust_level: document.getElementById('indoorDust').value,
          has_pets: document.getElementById('indoorPets').checked ? 1 : 0,
          smoking_exposure: document.getElementById('indoorSmoking').checked ? 1 : 0,
          has_air_purifier: document.getElementById('indoorPurifier').checked ? 1 : 0
        };

        try {
          const res = await window.PranvyraAPI.submitIndoorCheck(payload);
          if (res.success && res.assessment) {
            this.renderAssessment(res.assessment);
            window.PranvyraState.addPoints(20);
            window.PranvyraAPI.showToast('Indoor air audit evaluated! +20 Green Points awarded.', 'success');
          }
        } catch (error) {
          window.PranvyraAPI.showToast('Could not complete indoor audit.', 'error');
        }
      });
    }
  },

  async loadLatestCheck() {
    try {
      const res = await window.PranvyraAPI.getLatestIndoorCheck();
      if (res.success && res.assessment) {
        this.renderAssessment(res.assessment);
      }
    } catch (e) {
      console.warn("Could not load indoor check:", e);
    }
  },

  renderAssessment(assessment) {
    const scoreNum = document.getElementById('indoorScoreNum');
    const riskBadge = document.getElementById('indoorRiskBadge');
    const riskTitle = document.getElementById('indoorRiskTitle');
    const riskDesc = document.getElementById('indoorRiskDesc');
    const checklist = document.getElementById('indoorChecklist');

    if (scoreNum) {
      scoreNum.textContent = assessment.score;
      scoreNum.style.color = assessment.score_color || '#16A88A';
    }
    if (riskBadge) {
      riskBadge.textContent = assessment.risk_level;
      riskBadge.style.color = assessment.score_color || '#16A88A';
    }
    if (riskTitle) riskTitle.textContent = assessment.risk_level;
    
    if (checklist && assessment.actions) {
      checklist.innerHTML = '';
      assessment.actions.forEach(action => {
        const item = document.createElement('div');
        item.className = 'indoor-check-item';
        item.innerHTML = `
          <div class="item-head">
            <span class="item-title">${action.title}</span>
            <span class="badge-priority ${action.priority.toLowerCase()}">${action.priority}</span>
          </div>
          <p class="item-detail">${action.detail}</p>
        `;
        checklist.appendChild(item);
      });
    }

    if (window.lucide) {
      window.lucide.createIcons();
    }
  }
};
