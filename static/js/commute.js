/**
 * PRANVYRA Green Commute Comparator & What-If Simulator
 */
window.PranvyraCommute = {
  selectedTargetMode: 'metro',

  init() {
    this.bindEvents();
    this.updateComparisonAndSimulation();
  },

  bindEvents() {
    const slider = document.getElementById('commuteDistSlider');
    const modeSelect = document.getElementById('commuteCurrentMode');
    const passInput = document.getElementById('commutePassengers');
    const logBtn = document.getElementById('logGreenCommuteBtn');

    if (slider) {
      slider.addEventListener('input', (e) => {
        const valEl = document.getElementById('commuteDistVal');
        if (valEl) valEl.textContent = `${e.target.value} km`;
        const labelEl = document.getElementById('compareDistLabel');
        if (labelEl) labelEl.textContent = `${e.target.value} km`;
        this.updateComparisonAndSimulation();
      });
    }

    if (modeSelect) {
      modeSelect.addEventListener('change', () => this.updateComparisonAndSimulation());
    }

    if (passInput) {
      passInput.addEventListener('change', () => this.updateComparisonAndSimulation());
    }

    // What-if target mode chips
    document.querySelectorAll('.mode-chip').forEach(chip => {
      chip.addEventListener('click', (e) => {
        document.querySelectorAll('.mode-chip').forEach(c => c.classList.remove('active'));
        e.currentTarget.classList.add('active');
        this.selectedTargetMode = e.currentTarget.getAttribute('data-target-mode');
        this.runSimulationOnly();
      });
    });

    if (logBtn) {
      logBtn.addEventListener('click', async () => {
        const dist = parseFloat(document.getElementById('commuteDistSlider').value) || 14.5;
        const currentMode = document.getElementById('commuteCurrentMode').value;
        const targetMode = this.selectedTargetMode;

        try {
          const res = await window.PranvyraAPI.logGreenCommute(dist, currentMode, targetMode, window.PranvyraState.userId);
          if (res.success) {
            window.PranvyraState.addPoints(res.points_earned);
            window.PranvyraAPI.showToast(res.message, 'success');
            // Refresh impact metrics
            if (window.PranvyraImpact) {
              window.PranvyraImpact.loadSummary();
            }
          }
        } catch (e) {
          window.PranvyraAPI.showToast('Could not record green commute.', 'error');
        }
      });
    }
  },

  async updateComparisonAndSimulation() {
    const dist = parseFloat(document.getElementById('commuteDistSlider')?.value) || 14.5;
    const currentMode = document.getElementById('commuteCurrentMode')?.value || 'motorcycle';
    const passengers = parseInt(document.getElementById('commutePassengers')?.value) || 1;

    try {
      const res = await window.PranvyraAPI.compareCommute(dist, currentMode, passengers);
      if (res.success && res.result) {
        const cur = res.result.current_mode;
        const co2El = document.getElementById('currentTripCo2');
        const costEl = document.getElementById('currentTripCost');
        if (co2El) co2El.textContent = `${cur.emissions_kg} kg CO₂`;
        if (costEl) costEl.textContent = `₹${cur.cost_estimate}`;

        if (window.PranvyraCharts) {
          window.PranvyraCharts.initCommuteCompareChart(res.result);
        }
      }
    } catch (e) {
      console.warn("Failed to load commute comparison:", e);
    }

    this.runSimulationOnly();
  },

  async runSimulationOnly() {
    const dist = parseFloat(document.getElementById('commuteDistSlider')?.value) || 14.5;
    const currentMode = document.getElementById('commuteCurrentMode')?.value || 'motorcycle';
    const targetMode = this.selectedTargetMode;

    try {
      const simRes = await window.PranvyraAPI.simulateCommute(dist, currentMode, targetMode, 2);
      if (simRes.success && simRes.simulation) {
        const s = simRes.simulation;
        const tripEl = document.getElementById('simTripSavings');
        const monEl = document.getElementById('simMonthlySavings');
        const annEl = document.getElementById('simAnnualSavings');
        const treeEl = document.getElementById('simTreesEquiv');
        const expEl = document.getElementById('simExplanationText');

        if (tripEl) tripEl.textContent = `${s.trip_savings_kg} kg`;
        if (monEl) monEl.textContent = `${s.monthly_savings_kg} kg`;
        if (annEl) annEl.textContent = `${s.annual_savings_kg} kg`;
        if (treeEl) treeEl.textContent = `${s.trees_equivalent_annual}`;
        if (expEl) expEl.textContent = s.explanation;
      }
    } catch (e) {
      console.warn("Failed to run commute simulation:", e);
    }
  }
};

