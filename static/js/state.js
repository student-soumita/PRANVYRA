/**
 * PRANVYRA Global State Store
 * Open-Access Visitor Architecture — Strictly No Demo Accounts
 */
(function() {
  function generateVisitorId() {
    let id = localStorage.getItem('pranvyra_visitor_id');
    if (!id) {
      id = 'v-' + Math.random().toString(36).substring(2, 9) + '-' + Date.now().toString(36);
      localStorage.setItem('pranvyra_visitor_id', id);
    }
    return id;
  }

  window.PranvyraState = {
    visitorId: generateVisitorId(),
    activeView: 'home',
    theme: localStorage.getItem('pranvyra_theme') || 'dark',
    language: localStorage.getItem('pranvyra_lang') || 'en',
    
    // Visitor Profile (Real, dynamic, voluntarily set)
    profile: {
      visitor_id: null,
      display_name: 'Citizen Explorer',
      city: null,
      latitude: null,
      longitude: null,
      commute_distance_km: 10.0,
      primary_transport: 'public_transit',
      outdoor_hours: '1-2 hours',
      work_schedule: 'Hybrid / Office',
      ventilation_type: 'natural',
      cooking_fuel: 'lpg',
      green_points: 0,
      language_pref: 'en'
    },

    airQuality: null,
    weather: null,
    airwiseAction: null,
    breathBudget: null,
    isDataAvailable: true,
    activeReceipt: null,

    listeners: {},

    subscribe(event, callback) {
      if (!this.listeners[event]) {
        this.listeners[event] = [];
      }
      this.listeners[event].push(callback);
    },

    emit(event, data) {
      if (this.listeners[event]) {
        this.listeners[event].forEach(cb => {
          try {
            cb(data);
          } catch (e) {
            console.error(`Error in listener for ${event}:`, e);
          }
        });
      }
    },

    setProfile(profileData) {
      this.profile = { ...this.profile, ...profileData };
      if (profileData.language_pref) {
        this.setLanguage(profileData.language_pref, false);
      }
      this.emit('profile:updated', this.profile);
    },

    setAirQuality(aqiData) {
      this.airQuality = aqiData;
      this.isDataAvailable = aqiData && aqiData.is_available !== false;
      this.emit('aqi:updated', aqiData);
    },

    setWeather(weatherData) {
      this.weather = weatherData;
      this.emit('weather:updated', weatherData);
    },

    setView(viewName) {
      this.activeView = viewName;
      document.body.setAttribute('data-active-view', viewName);
      this.emit('view:changed', viewName);
    },

    setLanguage(lang, persist = true) {
      this.language = lang;
      if (persist) {
        localStorage.setItem('pranvyra_lang', lang);
      }
      this.emit('language:changed', lang);
    },

    addPoints(delta) {
      this.profile.green_points = Math.max(0, (this.profile.green_points || 0) + delta);
      this.emit('profile:updated', this.profile);
      this.emit('points:added', delta);
    },

    setActiveReceipt(receipt) {
      this.activeReceipt = receipt;
      this.emit('receipt:opened', receipt);
    }
  };

  // Sync visitorId
  window.PranvyraState.profile.visitor_id = window.PranvyraState.visitorId;
})();
