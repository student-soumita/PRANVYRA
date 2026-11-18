/**
 * PRANVYRA Air-Twin — Adaptive Personal Environmental Intelligence
 * Feature A: Adaptive Resilience Scoring & Hyperlocal Exposure Guidance
 */
window.PranvyraAirTwin = {
  currentTwin: null,

  async init() {
    this.bindEvents();
    await this.loadAirTwin();
  },

  bindEvents() {
    const form = document.getElementById('airTwinSettingsForm');
    if (form) {
      form.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.handleSaveSettings();
      });
    }

    const regForm = document.getElementById('optionalRegisterForm');
    if (regForm) {
      regForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        await this.handleOptionalRegister();
      });
    }

    // Subscribe to state changes (e.g. location updated from top bar)
    if (window.PranvyraState) {
      window.PranvyraState.subscribe('aqi:updated', () => {
        this.loadAirTwin();
      });
    }
  },

  async loadAirTwin() {
    try {
      const res = await window.PranvyraAPI.getAirTwin();
      if (res.success) {
        this.currentTwin = res.air_twin;
        this.renderTwin(res.air_twin, res.profile);
      }
    } catch (err) {
      console.warn('Could not load Air-Twin:', err);
    }
  },

  renderTwin(twin, profile) {
    if (twin) {
      const scoreEl = document.getElementById('twinScoreVal');
      if (scoreEl) {
        scoreEl.textContent = twin.resilience_score;
        scoreEl.className = 'twin-score-val';
        if (twin.resilience_score >= 75) scoreEl.classList.add('text-emerald');
        else if (twin.resilience_score >= 50) scoreEl.classList.add('text-amber');
        else scoreEl.classList.add('text-coral');
      }

      const vulnEl = document.getElementById('twinTransportVuln');
      if (vulnEl && twin.commute_vulnerability) {
        vulnEl.textContent = `${twin.commute_vulnerability.vulnerability_tier.toUpperCase()} — ${twin.commute_vulnerability.assessment}`;
      }

      const ventEl = document.getElementById('twinVentWindow');
      if (ventEl && twin.safe_ventilation_window) {
        ventEl.textContent = twin.safe_ventilation_window;
      }

      const exEl = document.getElementById('twinExerciseWindow');
      if (exEl && twin.optimal_exercise_window) {
        exEl.textContent = twin.optimal_exercise_window;
      }
    }

    if (profile) {
      const nameInp = document.getElementById('prefDisplayName');
      if (nameInp && profile.display_name) nameInp.value = profile.display_name;

      const cityInp = document.getElementById('prefCity');
      if (cityInp && profile.city) cityInp.value = profile.city;

      const distInp = document.getElementById('prefCommuteDist');
      if (distInp && profile.commute_distance_km) distInp.value = profile.commute_distance_km;

      const transInp = document.getElementById('prefTransport');
      if (transInp && profile.primary_transport) transInp.value = profile.primary_transport;

      const outInp = document.getElementById('prefOutdoorHours');
      if (outInp && profile.outdoor_hours) outInp.value = profile.outdoor_hours;

      const ventInp = document.getElementById('prefVentilation');
      if (ventInp && profile.ventilation_type) ventInp.value = profile.ventilation_type;

      const cookInp = document.getElementById('prefCookingFuel');
      if (cookInp && profile.cooking_fuel) cookInp.value = profile.cooking_fuel;

      const langInp = document.getElementById('prefLanguage');
      if (langInp && profile.language_pref) langInp.value = profile.language_pref;
    }
  },

  async handleSaveSettings() {
    const data = {
      display_name: document.getElementById('prefDisplayName').value.trim() || 'Citizen Explorer',
      city: document.getElementById('prefCity').value.trim() || null,
      commute_distance_km: parseFloat(document.getElementById('prefCommuteDist').value) || 10.0,
      primary_transport: document.getElementById('prefTransport').value,
      outdoor_hours: document.getElementById('prefOutdoorHours').value.trim(),
      ventilation_type: document.getElementById('prefVentilation').value,
      cooking_fuel: document.getElementById('prefCookingFuel').value,
      language_pref: document.getElementById('prefLanguage').value
    };

    try {
      const res = await window.PranvyraAPI.updateUserProfile(data);
      if (res.success) {
        window.PranvyraAPI.showToast('Air-Twin profile updated & adapted!', 'success');
        if (window.PranvyraState) {
          window.PranvyraState.setProfile(res.profile);
        }
        await this.loadAirTwin();
      }
    } catch (err) {
      console.error('Error saving Air-Twin profile:', err);
    }
  },

  async handleOptionalRegister() {
    const username = document.getElementById('optUsername').value.trim();
    const email = document.getElementById('optEmail').value.trim();
    const password = document.getElementById('optPassword').value.trim();

    if (!username || !email || !password) {
      window.PranvyraAPI.showToast('Please fill in username, email, and password.', 'warning');
      return;
    }

    try {
      const res = await window.PranvyraAPI.registerOptionalAccount(email, username, password);
      if (res.success) {
        window.PranvyraAPI.showToast(res.message, 'success');
        document.getElementById('optionalRegisterForm').reset();
      }
    } catch (err) {
      console.error('Optional register error:', err);
    }
  }
};

document.addEventListener('DOMContentLoaded', () => {
  window.PranvyraAirTwin.init();
});

