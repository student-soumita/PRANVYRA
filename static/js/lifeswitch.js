/**
 * PRANVYRA Life-Switch — Environmental Decision Simulator
 * Feature C: Interactive What-If Engine & Verified Emission Calculations
 */
window.PranvyraLifeSwitch = {
  catalog: [],
  activeSwitchKey: 'commute_moto_to_metro',
  activeSwitch: null,
  activeSimulation: null,
  sliderDebounceTimer: null,

  async init() {
    this.bindEvents();
    await this.loadCatalog();
  },

  bindEvents() {
    const slider = document.getElementById('simParamSlider');
    if (slider) {
      slider.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        this.updateSliderDisplay(val);
        
        clearTimeout(this.sliderDebounceTimer);
        this.sliderDebounceTimer = setTimeout(() => {
          this.runSimulation(this.activeSwitchKey, val);
        }, 200);
      });
    }

    const commitBtn = document.getElementById('simCommitBtn');
    if (commitBtn) {
      commitBtn.addEventListener('click', async () => {
        await this.handleCommitSwitch();
      });
    }
  },

  async loadCatalog() {
    try {
      const res = await window.PranvyraAPI.getLifeSwitchCatalog();
      if (res.success && res.switches) {
        this.catalog = res.switches;
        this.renderTabs();
        if (this.catalog.length > 0) {
          this.selectSwitch(this.catalog[0].key);
        }
      }
    } catch (err) {
      console.error('Failed to load Life-Switch catalog:', err);
    }
  },

  renderTabs() {
    const container = document.getElementById('lifeSwitchTabs');
    if (!container) return;

    container.innerHTML = '';
    this.catalog.forEach(sw => {
      const tab = document.createElement('div');
      tab.className = `switch-tab ${sw.key === this.activeSwitchKey ? 'active' : ''}`;
      tab.setAttribute('data-key', sw.key);
      tab.innerHTML = `
        <span class="tab-category">${sw.category}</span>
        <h4 class="tab-title">${sw.title}</h4>
        <span class="tab-contrast">${sw.current_habit.split('(')[0]} &rarr; ${sw.alternative_habit.split('(')[0]}</span>
      `;
      tab.addEventListener('click', () => {
        this.selectSwitch(sw.key);
      });
      container.appendChild(tab);
    });
  },

  async selectSwitch(switchKey) {
    this.activeSwitchKey = switchKey;
    this.activeSwitch = this.catalog.find(s => s.key === switchKey) || this.catalog[0];

    // Update active tab style
    document.querySelectorAll('.switch-tab').forEach(t => {
      t.classList.toggle('active', t.getAttribute('data-key') === switchKey);
    });

    // Update playground UI headers
    const catEl = document.getElementById('simCategory');
    if (catEl) catEl.textContent = this.activeSwitch.category;

    const titleEl = document.getElementById('simTitle');
    if (titleEl) titleEl.textContent = this.activeSwitch.title;

    const curHabitEl = document.getElementById('simCurrentHabit');
    if (curHabitEl) curHabitEl.textContent = this.activeSwitch.current_habit;

    const altHabitEl = document.getElementById('simAlternativeHabit');
    if (altHabitEl) altHabitEl.textContent = this.activeSwitch.alternative_habit;

    // Configure slider
    const param = this.activeSwitch.parameter;
    const slider = document.getElementById('simParamSlider');
    const labelEl = document.getElementById('simParamLabel');

    if (param && slider && labelEl) {
      labelEl.textContent = `${param.label}:`;
      slider.min = param.min;
      slider.max = param.max;
      slider.step = param.step;
      slider.value = param.default;
      this.updateSliderDisplay(param.default, param.unit);
    }

    // Run simulation
    const initVal = param ? param.default : null;
    await this.runSimulation(switchKey, initVal);
  },

  updateSliderDisplay(val, unit = null) {
    const display = document.getElementById('simParamValDisplay');
    if (!display) return;
    
    if (!unit && this.activeSwitch && this.activeSwitch.parameter) {
      unit = this.activeSwitch.parameter.unit;
    }
    display.textContent = `${val} ${unit || ''}`;
  },

  async runSimulation(switchKey, paramVal) {
    try {
      const res = await window.PranvyraAPI.simulateLifeSwitch(switchKey, paramVal);
      if (res.success && res.simulation) {
        this.activeSimulation = res.simulation;
        this.renderSimulationResults(res.simulation);
      }
    } catch (err) {
      console.error('Simulation error:', err);
    }
  },

  renderSimulationResults(sim) {
    const m = sim.metrics;

    const monthlyEl = document.getElementById('simMetricMonthly');
    if (monthlyEl) {
      monthlyEl.textContent = `${m.monthly_savings_kg} kg`;
    }

    const annualEl = document.getElementById('simMetricAnnual');
    if (annualEl) {
      annualEl.textContent = `${m.annual_savings_kg} kg`;
    }

    const methodEl = document.getElementById('simMethodology');
    if (methodEl) {
      methodEl.textContent = m.methodology;
    }

    const assumptionsEl = document.getElementById('simAssumptions');
    if (assumptionsEl) {
      assumptionsEl.textContent = m.assumptions;
    }
  },

  async handleCommitSwitch() {
    if (!this.activeSwitchKey) return;
    const slider = document.getElementById('simParamSlider');
    const paramVal = slider ? parseFloat(slider.value) : null;

    try {
      const res = await window.PranvyraAPI.commitLifeSwitch(this.activeSwitchKey, paramVal);
      if (res.success && res.receipt) {
        window.PranvyraAPI.showToast(res.message, 'success');
        if (window.PranvyraState) {
          window.PranvyraState.addPoints(res.points_earned || 30);
        }
        // Open receipt modal
        if (window.PranvyraImpact && window.PranvyraImpact.openReceiptModal) {
          window.PranvyraImpact.openReceiptModal(res.receipt);
        }
      }
    } catch (err) {
      console.error('Commit switch error:', err);
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  window.PranvyraLifeSwitch.init();
});

