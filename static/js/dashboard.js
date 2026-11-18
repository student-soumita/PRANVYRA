/**
 * PRANVYRA Dashboard Controller
 * Open-Access: Renders live air quality, weather, pollutants, map & trends.
 * Shows unavailable-data state when API offline (never fakes data).
 */
window.PranvyraDashboard = {
  currentMetric: 'aqi',
  cachedData: null,

  init() {
    this.bindEvents();
    window.addEventListener('pranvyra:language_changed', () => {
      if (this.cachedData) {
        this.render(this.cachedData);
      }
    });
  },

  bindEvents() {
    const refreshBtn = document.getElementById('refreshDashboardBtn');
    if (refreshBtn) {
      refreshBtn.addEventListener('click', () => {
        window.PranvyraApp.loadDashboardData();
        window.PranvyraAPI.showToast('Environmental data refreshed from atmospheric assimilation models.', 'success');
      });
    }

    const recenterBtn = document.getElementById('recenterMapBtn');
    if (recenterBtn) {
      recenterBtn.addEventListener('click', () => {
        const p = window.PranvyraState.profile;
        const aqi = window.PranvyraState.airQuality?.aqi || 50;
        if (p.latitude && p.longitude && window.PranvyraMap) {
          window.PranvyraMap.updateLocation(p.latitude, p.longitude, aqi);
        }
      });
    }

    // Chart metric toggles
    document.querySelectorAll('[data-chart-metric]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('[data-chart-metric]').forEach(b => b.classList.remove('active'));
        e.currentTarget.classList.add('active');
        const metric = e.currentTarget.getAttribute('data-chart-metric');
        this.currentMetric = metric;
        if (window.PranvyraState.airQuality?.hourly_trend) {
          window.PranvyraCharts.initHourlyTrendChart(window.PranvyraState.airQuality.hourly_trend, metric);
        }
      });
    });
  },

  render(data) {
    if (!data) return;
    this.cachedData = data;

    // Handle requires_location state
    if (data.requires_location) {
      this.showLocationRequired();
      return;
    }

    const aqi = data.air_quality;
    const weather = data.weather;
    const airwise = data.airwise_action;
    const budget = data.breath_budget;
    const profile = data.profile;

    // Handle data unavailable
    if (aqi && aqi.is_available === false) {
      this.showDataUnavailable();
    } else {
      this.hideDataUnavailable();
    }

    // Dynamic translations
    const catKey = aqi ? ('aqi_cat_' + (aqi.category || '').toLowerCase().replace(/[^a-z0-9]/g, '_')) : '';
    const translatedCategory = (window.PranvyraI18n && catKey) ? window.PranvyraI18n.t(catKey, aqi.category) : (aqi?.category || '');

    // Show AQI pill in topbar
    const aqiPill = document.getElementById('topbarAqiPill');
    if (aqiPill && aqi && aqi.is_available !== false) {
      aqiPill.style.display = 'flex';
    }

    // 1. Topbar Elements
    const topAqiVal = document.getElementById('topbarAqiValue');
    const topAqiCat = document.getElementById('topbarAqiCat');
    const topCity = document.getElementById('topbarCityName');

    if (topAqiVal && aqi) topAqiVal.textContent = aqi.aqi;
    if (topAqiCat && aqi) topAqiCat.textContent = translatedCategory;
    if (topCity && profile) topCity.textContent = profile.city || 'Select Your Location';

    // 2. Hero Widget on Landing
    const heroAqi = document.getElementById('heroWidgetAqi');
    const heroCat = document.getElementById('heroWidgetCategory');
    const heroCity = document.getElementById('heroWidgetCity');
    const heroAction = document.getElementById('heroWidgetAction');

    if (heroAqi && aqi) heroAqi.textContent = aqi.aqi;
    if (heroCat && aqi) {
      heroCat.textContent = translatedCategory;
      heroCat.style.color = aqi.color;
      heroCat.style.borderColor = aqi.color;
    }
    if (heroCity && profile) heroCity.textContent = profile.city || '';
    if (heroAction && airwise) heroAction.textContent = `"${airwise.action}"`;

    // 3. AQI Hero Card
    const dashAqiVal = document.getElementById('dashAqiValue');
    const dashAqiCat = document.getElementById('dashAqiCatPill');
    const dashAdvice = document.getElementById('dashAqiHealthAdvice');
    const dashSource = document.getElementById('dashDataSource');
    const marker = document.getElementById('aqiSpectrumMarker');

    if (dashAqiVal && aqi) {
      dashAqiVal.textContent = aqi.aqi;
      dashAqiVal.style.color = aqi.color;
    }
    if (dashAqiCat && aqi) {
      dashAqiCat.textContent = translatedCategory;
      dashAqiCat.style.color = aqi.color;
      dashAqiCat.style.borderColor = aqi.color;
    }
    if (dashAdvice && aqi) dashAdvice.textContent = aqi.health_advice;
    if (dashSource && aqi) {
      dashSource.innerHTML = `<i data-lucide="database"></i> ${aqi.data_source}`;
    }

    if (marker && aqi) {
      const pct = Math.min(100, Math.max(0, (aqi.aqi / 300) * 100));
      marker.style.left = `${pct}%`;
      marker.style.borderColor = aqi.color;
    }

    // 4. AIRWISE Action Card
    if (airwise) {
      const urgency = document.getElementById('airwiseUrgency');
      const title = document.getElementById('airwiseTitle');
      const problem = document.getElementById('airwiseProblem');
      const action = document.getElementById('airwiseActionText');
      const benefit = document.getElementById('airwiseBenefit');
      const confidence = document.getElementById('airwiseConfidence');

      const pKey = 'priority_' + (airwise.urgency || '').toLowerCase();
      const translatedUrgency = (window.PranvyraI18n) ? window.PranvyraI18n.t(pKey, `${airwise.urgency} Priority`) : `${airwise.urgency} Priority`;

      if (urgency) {
        urgency.textContent = translatedUrgency;
        urgency.className = `badge-priority ${airwise.urgency.toLowerCase()}`;
      }
      if (title) title.textContent = airwise.title;
      if (problem) problem.textContent = airwise.problem;
      if (action) action.textContent = airwise.action;
      if (benefit) benefit.innerHTML = `<i data-lucide="check-circle-2"></i> ${airwise.expected_benefit}`;
      if (confidence) confidence.textContent = `${airwise.confidence}`;
    }

    // 5. Breath Budget Exposure Card
    if (budget) {
      const bPct = document.getElementById('dashBudgetPct');
      const bPill = document.getElementById('dashBudgetStatusPill');
      const bHours = document.getElementById('dashBudgetOutdoorHrs');
      const bMode = document.getElementById('dashBudgetTransportMode');
      const bRem = document.getElementById('dashBudgetRemaining');
      const bSum = document.getElementById('dashBudgetSummary');

      const bKey = 'budget_status_' + (budget.budget_status || '').toLowerCase().replace(/[^a-z0-9]/g, '_');
      const translatedStatus = (window.PranvyraI18n) ? window.PranvyraI18n.t(bKey, budget.budget_status) : budget.budget_status;

      if (bPct) {
        bPct.textContent = `${budget.budget_used_pct}%`;
        bPct.style.color = budget.badge_color;
      }
      if (bPill) {
        bPill.textContent = translatedStatus;
        bPill.style.color = budget.badge_color;
      }
      if (bHours) bHours.textContent = `${budget.outdoor_hours_estimated} hrs / day`;
      if (bMode && profile) bMode.textContent = (profile.primary_transport || 'public_transit').toUpperCase();
      if (bRem) bRem.textContent = `${budget.budget_remaining_pct}%`;
      if (bSum) bSum.textContent = budget.summary;
    }

    // 6. Weather Ribbon
    if (weather) {
      const wTemp = document.getElementById('weatherTemp');
      const wHum = document.getElementById('weatherHumidity');
      const wWind = document.getElementById('weatherWind');
      const wWindDir = document.getElementById('weatherWindDir');
      const wDesc = document.getElementById('weatherDesc');

      const wCodeKey = 'weather_code_' + weather.weather_code;
      const translatedWeather = (window.PranvyraI18n) ? window.PranvyraI18n.t(wCodeKey, weather.weather_desc) : weather.weather_desc;

      if (wTemp) wTemp.textContent = `${weather.temperature}°C`;
      if (wHum) wHum.textContent = `${weather.humidity}%`;
      if (wWind) wWind.textContent = `${weather.wind_speed} km/h`;
      if (wWindDir) wWindDir.textContent = `${weather.wind_direction}°`;
      if (wDesc) wDesc.textContent = translatedWeather;
    }

    // 7. 6 Pollutants Matrix
    if (aqi && aqi.pollutants) {
      const p = aqi.pollutants;
      this.updatePollutantCard('Pm25', p.pm25, 100);
      this.updatePollutantCard('Pm10', p.pm10, 200);
      this.updatePollutantCard('No2', p.no2, 80);
      this.updatePollutantCard('O3', p.o3, 120);
      this.updatePollutantCard('Co', p.co, 4000);
      this.updatePollutantCard('So2', p.so2, 50);
    }

    // 8. Leaflet Map
    if (window.PranvyraMap && profile) {
      if (!window.PranvyraMap.map) {
        window.PranvyraMap.init(profile.latitude, profile.longitude, aqi ? aqi.aqi : 50);
      } else {
        window.PranvyraMap.updateLocation(profile.latitude, profile.longitude, aqi ? aqi.aqi : 50);
      }
    }

    // 9. 24-Hour Trend Chart
    if (window.PranvyraCharts && aqi && aqi.hourly_trend) {
      window.PranvyraCharts.initHourlyTrendChart(aqi.hourly_trend, this.currentMetric);
    }

    // Update assistant context badges
    const chatCity = document.getElementById('chatCityBadge');
    const chatAqi = document.getElementById('chatAqiBadge');
    if (chatCity && profile) chatCity.textContent = profile.city || '';
    if (chatAqi && aqi) chatAqi.textContent = aqi.aqi;

    if (window.lucide) {
      window.lucide.createIcons();
    }
  },

  showLocationRequired() {
    // Location not set — guide user to enter city or use geolocation
    const topCity = document.getElementById('topbarCityName');
    if (topCity) topCity.textContent = 'Select Your Location';
  },

  showDataUnavailable() {
    const dashAdvice = document.getElementById('dashAqiHealthAdvice');
    if (dashAdvice) {
      dashAdvice.textContent = 'Live atmospheric data is currently unavailable for this location. Please check your connection or try another city.';
    }
  },

  hideDataUnavailable() {
    // No-op; normal render flow handles this
  },

  updatePollutantCard(key, polData, maxScale) {
    if (!polData) return;
    const valEl = document.getElementById(`polVal${key}`);
    const barEl = document.getElementById(`polBar${key}`);
    if (valEl) valEl.textContent = polData.value;
    if (barEl) {
      const pct = Math.min(100, Math.max(10, Math.round((polData.value / maxScale) * 100)));
      barEl.style.width = `${pct}%`;
    }
  }
};
