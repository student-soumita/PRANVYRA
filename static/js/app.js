/**
 * PRANVYRA Main Orchestrator & View Router
 * Open-Access Architecture: No demo accounts, no mandatory login.
 * Any visitor can enter their city and immediately use all features.
 */
window.PranvyraApp = {

  async init() {
    this.bindNavigation();
    this.bindThemeToggle();
    this.bindCitySearch();
    this.bindLocationOnboarding();

    // Subscribe to state changes
    if (window.PranvyraState) {
      window.PranvyraState.subscribe('profile:updated', (profile) => {
        this.syncProfileUI(profile);
      });
      window.PranvyraState.subscribe('points:added', () => {
        this.syncProfileUI(window.PranvyraState.profile);
      });
    }

    // Initialize sub-modules
    if (window.PranvyraDashboard) window.PranvyraDashboard.init();
    if (window.PranvyraAssistant) window.PranvyraAssistant.init();
    if (window.PranvyraPlanner) window.PranvyraPlanner.init();
    if (window.PranvyraIndoor) window.PranvyraIndoor.init();
    if (window.PranvyraImpact) window.PranvyraImpact.init();
    if (window.PranvyraCommunity) window.PranvyraCommunity.init();
    // BreathRoute, LifeSwitch, AirTwin self-init on DOMContentLoaded

    // Load visitor profile first
    await this.loadVisitorProfile();

    // Determine if user has a location set; if so, load dashboard
    const profile = window.PranvyraState.profile;
    if (profile && profile.latitude && profile.longitude) {
      await this.loadDashboardData();
    } else {
      // Benchmark fallback: load baseline atmospheric intelligence so dashboard initializes immediately
      await this.loadDashboardData();
    }

    // Check initial route hash (defaults to 'dashboard' for authenticated experience)
    const initialHash = window.location.hash.replace('#', '') || 'dashboard';
    this.switchView(initialHash);

    if (window.lucide) {
      window.lucide.createIcons();
    }
  },

  async loadVisitorProfile() {
    try {
      const res = await window.PranvyraAPI.getUserProfile();
      if (res && res.success && res.profile) {
        window.PranvyraState.setProfile(res.profile);
        this.syncProfileUI(res.profile);
        // Load saved user language preference
        if (res.profile.language_pref && window.PranvyraI18n && window.PranvyraI18n.currentLanguage !== res.profile.language_pref) {
          window.PranvyraI18n.setLanguage(res.profile.language_pref);
        }
      }
    } catch (e) {
      console.warn("Could not load visitor profile:", e);
    }
  },

  async loadDashboardData() {
    try {
      const p = window.PranvyraState.profile;
      const data = await window.PranvyraAPI.getDashboardOverview(p.latitude, p.longitude, p.city);

      if (data && data.success) {
        // Update profile from server
        if (data.profile) {
          window.PranvyraState.setProfile(data.profile);
        }

        // Handle requires_location
        if (data.requires_location) {
          if (window.PranvyraDashboard) {
            window.PranvyraDashboard.render(data);
          }
          return;
        }

        // Set environmental data
        if (data.air_quality) window.PranvyraState.setAirQuality(data.air_quality);
        if (data.weather) window.PranvyraState.setWeather(data.weather);
        window.PranvyraState.airwiseAction = data.airwise_action;
        window.PranvyraState.breathBudget = data.breath_budget;

        if (window.PranvyraDashboard) {
          window.PranvyraDashboard.render(data);
        }
      }
    } catch (e) {
      console.warn("Could not load dashboard overview:", e);
    }
  },

  async setLocation(cityName, lat, lon) {
    // Update state
    window.PranvyraState.setProfile({
      city: cityName,
      latitude: lat,
      longitude: lon
    });

    // Persist on server
    try {
      await window.PranvyraAPI.updateUserProfile({
        city: cityName,
        latitude: lat,
        longitude: lon
      });
    } catch (e) {
      console.warn("Could not persist location:", e);
    }

    // Reload dashboard
    window.PranvyraAPI.showToast(`Loading environmental data for ${cityName}...`, 'info');
    await this.loadDashboardData();

    // Re-center map
    if (window.PranvyraMap) {
      window.PranvyraMap.updateLocation(lat, lon, window.PranvyraState.airQuality?.aqi || 50);
    }
  },

  // ===================== NAVIGATION =====================
  bindNavigation() {
    // Sidebar nav links
    document.querySelectorAll('[data-nav]').forEach(el => {
      el.addEventListener('click', (e) => {
        e.preventDefault();
        const targetView = el.getAttribute('data-nav');
        this.switchView(targetView);
        window.location.hash = targetView;

        // Close mobile sidebar if open
        const sidebar = document.getElementById('appSidebar');
        if (sidebar) sidebar.classList.remove('open');
      });
    });

    // Landing Page Hero CTA: "Explore My Air"
    const exploreBtn = document.getElementById('heroExploreAqiBtn');
    if (exploreBtn) {
      exploreBtn.addEventListener('click', async () => {
        const heroInput = document.getElementById('heroLocationInput');
        const query = heroInput ? heroInput.value.trim() : '';

        if (query.length >= 2) {
          // Search and select first result
          try {
            const res = await window.PranvyraAPI.searchCities(query);
            if (res && res.results && res.results.length > 0) {
              const city = res.results[0];
              await this.setLocation(city.name, city.latitude, city.longitude);
              this.switchView('dashboard');
              window.location.hash = 'dashboard';
              return;
            }
          } catch (e) {
            console.warn("Hero city search failed:", e);
          }
        }

        // If no location entered, just navigate if location already set
        if (window.PranvyraState.profile.latitude) {
          this.switchView('dashboard');
          window.location.hash = 'dashboard';
        } else {
          window.PranvyraAPI.showToast('Please enter a city or locality to explore air quality.', 'warning');
        }
      });
    }

    // Hero "Discover How It Works"
    const howItWorksBtn = document.getElementById('heroHowItWorksBtn');
    if (howItWorksBtn) {
      howItWorksBtn.addEventListener('click', () => {
        const sec = document.getElementById('howItWorksSection');
        if (sec) sec.scrollIntoView({ behavior: 'smooth' });
      });
    }

    // Hero Live Widget → Dashboard
    const heroWidgetBtn = document.getElementById('heroWidgetGoDashboard');
    if (heroWidgetBtn) {
      heroWidgetBtn.addEventListener('click', () => {
        this.switchView('dashboard');
        window.location.hash = 'dashboard';
      });
    }

    // Mobile Sidebar Toggles
    const openBtn = document.getElementById('sidebarOpenBtn');
    const closeBtn = document.getElementById('sidebarCloseBtn');
    const sidebar = document.getElementById('appSidebar');

    if (openBtn && sidebar) {
      openBtn.addEventListener('click', () => sidebar.classList.add('open'));
    }
    if (closeBtn && sidebar) {
      closeBtn.addEventListener('click', () => sidebar.classList.remove('open'));
    }

    // Logout Buttons (Sidebar and Topbar)
    const handleLogout = async () => {
      if (window.PranvyraAPI && window.PranvyraAPI.logout) {
        await window.PranvyraAPI.logout();
      } else {
        window.location.href = '/login';
      }
    };

    const sidebarLogout = document.getElementById('sidebarLogoutBtn');
    if (sidebarLogout) {
      sidebarLogout.addEventListener('click', handleLogout);
    }
    const topbarLogout = document.getElementById('topbarLogoutBtn');
    if (topbarLogout) {
      topbarLogout.addEventListener('click', handleLogout);
    }

    // Window hashchange
    window.addEventListener('hashchange', () => {
      const hash = window.location.hash.replace('#', '') || 'overview';
      this.switchView(hash);
    });
  },

  switchView(viewName) {
    const validViews = [
      'overview', 'dashboard', 'assistant', 'planner', 'indoor',
      'breathroute', 'lifeswitch', 'impact', 'community',
      'airtwin', 'pollution-guide'
    ];
    const activeView = validViews.includes(viewName) ? viewName : 'overview';

    // Update panel active states
    document.querySelectorAll('.view-panel').forEach(panel => {
      panel.classList.remove('active');
    });

    const targetPanel = document.getElementById(`view-${activeView}`);
    if (targetPanel) {
      targetPanel.classList.add('active');
    }

    // Update sidebar nav items
    document.querySelectorAll('.sidebar-nav .nav-item').forEach(item => {
      if (item.getAttribute('data-nav') === activeView) {
        item.classList.add('active');
      } else {
        item.classList.remove('active');
      }
    });

    window.PranvyraState.setView(activeView);

    // Stop voice recognition and speech synthesis if navigating away from assistant
    if (activeView !== 'assistant' && window.PranvyraAssistant) {
      if (window.PranvyraAssistant.isRecording) window.PranvyraAssistant.stopVoiceInput();
      if (window.PranvyraAssistant.isSpeaking) window.PranvyraAssistant.stopSpeech();
    }

    // Ensure dashboard data and map size are refreshed if opening dashboard
    if (activeView === 'dashboard') {
      if (!window.PranvyraState.airQuality) {
        this.loadDashboardData();
      }
      if (window.PranvyraMap) {
        setTimeout(() => {
          window.PranvyraMap.invalidateSize();
        }, 120);
      }
    }

    // Lazy-load module data on first view
    if (activeView === 'impact' && window.PranvyraImpact) {
      window.PranvyraImpact.loadSummary();
      window.PranvyraImpact.loadReceipts();
    }
    if (activeView === 'community' && window.PranvyraCommunity) {
      window.PranvyraCommunity.loadPulse();
      window.PranvyraCommunity.loadChallenges();
    }
    if (activeView === 'airtwin' && window.PranvyraAirTwin) {
      window.PranvyraAirTwin.loadAirTwin();
    }

    // Scroll window to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
  },

  // ===================== LOCATION ONBOARDING =====================
  bindLocationOnboarding() {
    // Hero geolocation button
    const geoBtn = document.getElementById('heroGeolocateBtn');
    if (geoBtn) {
      geoBtn.addEventListener('click', () => this.handleGeolocation());
    }

    // Topbar "Detect Location" button
    const detectBtn = document.getElementById('detectLocationBtn');
    if (detectBtn) {
      detectBtn.addEventListener('click', () => {
        this.handleGeolocation();
        const flyout = document.getElementById('citySearchFlyout');
        if (flyout) flyout.classList.remove('open');
      });
    }

    // Quick city chips (in flyout)
    document.querySelectorAll('.quick-chip').forEach(chip => {
      chip.addEventListener('click', async () => {
        const city = chip.getAttribute('data-city');
        const lat = parseFloat(chip.getAttribute('data-lat'));
        const lon = parseFloat(chip.getAttribute('data-lon'));
        if (city && lat && lon) {
          const flyout = document.getElementById('citySearchFlyout');
          if (flyout) flyout.classList.remove('open');
          await this.setLocation(city, lat, lon);
          this.switchView('dashboard');
          window.location.hash = 'dashboard';
        }
      });
    });
  },

  handleGeolocation() {
    if (!navigator.geolocation) {
      window.PranvyraAPI.showToast('Geolocation is not supported by your browser.', 'warning');
      return;
    }

    window.PranvyraAPI.showToast('Detecting your location...', 'info');

    navigator.geolocation.getCurrentPosition(
      async (pos) => {
        const lat = pos.coords.latitude;
        const lon = pos.coords.longitude;

        try {
          const res = await window.PranvyraAPI.searchCities(`${lat},${lon}`);
          const cityName = (res && res.results && res.results.length > 0 && res.results[0].name) ? res.results[0].name : 'My Location';
          await this.setLocation(cityName, lat, lon);
          this.switchView('dashboard');
          window.location.hash = 'dashboard';
        } catch (e) {
          await this.setLocation('My Location', lat, lon);
          this.switchView('dashboard');
          window.location.hash = 'dashboard';
        }
      },
      (err) => {
        let msg = 'Location permission denied. Please enter your city manually in the search box.';
        if (err.code === 2) msg = 'Location unavailable. Please select your city manually.';
        else if (err.code === 3) msg = 'Location request timed out. Please select your city manually.';
        window.PranvyraAPI.showToast(msg, 'warning');
        console.warn("Geolocation error:", err);
      },
      { enableHighAccuracy: false, timeout: 12000, maximumAge: 60000 }
    );
  },

  // ===================== CITY SEARCH (TOPBAR) =====================
  bindCitySearch() {
    const topbarWrap = document.getElementById('topbarLocationBtn');
    const toggleBtn = document.getElementById('citySearchToggleBtn');
    const flyout = document.getElementById('citySearchFlyout');
    const input = document.getElementById('citySearchInput');
    const resultsList = document.getElementById('cityResultsList');

    const openFlyout = (e) => {
      e.stopPropagation();
      if (!flyout) return;
      flyout.classList.toggle('open');
      if (flyout.classList.contains('open') && input) {
        setTimeout(() => input.focus(), 50);
      }
    };

    if (topbarWrap && flyout) {
      topbarWrap.addEventListener('click', (e) => {
        // Prevent re-toggling when interacting with inside elements of flyout
        if (flyout.contains(e.target)) return;
        openFlyout(e);
      });

      document.addEventListener('click', (e) => {
        if (!flyout.contains(e.target) && !topbarWrap.contains(e.target)) {
          flyout.classList.remove('open');
        }
      });
    }

    if (input && resultsList) {
      let debounceTimeout;
      input.addEventListener('input', () => {
        clearTimeout(debounceTimeout);
        debounceTimeout = setTimeout(async () => {
          const q = input.value.trim();
          if (q.length < 2) return;

          try {
            const res = await window.PranvyraAPI.searchCities(q);
            if (res && res.results) {
              resultsList.innerHTML = '';
              res.results.forEach(city => {
                const item = document.createElement('div');
                item.className = 'city-result-item';
                item.innerHTML = `
                  <span><strong>${city.name}</strong>, ${city.country}</span>
                  <small style="color: #648278;">${Math.round(city.latitude * 100) / 100}°, ${Math.round(city.longitude * 100) / 100}°</small>
                `;

                item.addEventListener('click', async () => {
                  flyout.classList.remove('open');
                  input.value = '';
                  resultsList.innerHTML = '';
                  await this.setLocation(city.name, city.latitude, city.longitude);
                });

                resultsList.appendChild(item);
              });
            }
          } catch (e) {
            console.warn("City search failed:", e);
          }
        }, 300);
      });
    }
  },

  // ===================== THEME =====================
  bindThemeToggle() {
    const toggleBtn = document.getElementById('themeToggleBtn');
    const themeIcon = document.getElementById('themeIcon');
    const savedTheme = localStorage.getItem('pranvyra_theme') || 'dark';

    if (savedTheme === 'light') {
      document.body.classList.remove('theme-dark');
      document.body.classList.add('theme-light');
      if (themeIcon) themeIcon.setAttribute('data-lucide', 'moon');
    } else {
      document.body.classList.remove('theme-light');
      document.body.classList.add('theme-dark');
      if (themeIcon) themeIcon.setAttribute('data-lucide', 'sun');
    }

    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        const isDark = document.body.classList.contains('theme-dark');
        if (isDark) {
          document.body.classList.remove('theme-dark');
          document.body.classList.add('theme-light');
          localStorage.setItem('pranvyra_theme', 'light');
          if (themeIcon) themeIcon.setAttribute('data-lucide', 'moon');
        } else {
          document.body.classList.remove('theme-light');
          document.body.classList.add('theme-dark');
          localStorage.setItem('pranvyra_theme', 'dark');
          if (themeIcon) themeIcon.setAttribute('data-lucide', 'sun');
        }
        if (window.lucide) window.lucide.createIcons();
      });
    }
  },

  // ===================== PROFILE UI SYNC =====================
  syncProfileUI(profile) {
    if (!profile) return;

    const nameEl = document.getElementById('sidebarUserName');
    const ptsEl = document.getElementById('sidebarUserPoints');
    const avatarEl = document.getElementById('userAvatar');
    const topCity = document.getElementById('topbarCityName');

    const displayName = profile.display_name || 'Citizen Explorer';
    const greenPts = profile.green_points || 0;
    const city = profile.city || 'Select Your Location';

    if (nameEl) nameEl.textContent = displayName;
    if (ptsEl) ptsEl.innerHTML = `<i data-lucide="sparkles"></i> ${greenPts} pts`;
    if (topCity) topCity.textContent = city;
    if (avatarEl) {
      const parts = displayName.trim().split(' ');
      const initials = parts.length > 1 ? parts[0][0] + parts[1][0] : parts[0].slice(0, 2);
      avatarEl.textContent = initials.toUpperCase();
    }

    if (window.lucide) {
      window.lucide.createIcons();
    }
  }
};

// Start PRANVYRA when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.PranvyraApp.init();
});
