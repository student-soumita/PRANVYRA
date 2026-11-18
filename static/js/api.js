/**
 * PRANVYRA API Client & Toast Notification Service
 * Open-Access Architecture: Sends X-Visitor-Id with all API calls.
 */
window.PranvyraAPI = {
  
  showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let iconName = 'info';
    if (type === 'success') iconName = 'check-circle-2';
    if (type === 'warning') iconName = 'alert-triangle';
    if (type === 'error') iconName = 'alert-circle';
    
    toast.innerHTML = `
      <i data-lucide="${iconName}"></i>
      <span>${message}</span>
    `;
    container.appendChild(toast);
    
    if (window.lucide) {
      window.lucide.createIcons({ root: toast });
    }
    
    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateY(10px)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  },

  getVisitorId() {
    return window.PranvyraState ? window.PranvyraState.visitorId : (localStorage.getItem('pranvyra_visitor_id') || 'anonymous');
  },

  async request(endpoint, options = {}) {
    try {
      const visitorId = this.getVisitorId();
      const headers = {
        'Content-Type': 'application/json',
        'X-Visitor-Id': visitorId,
        ...(options.headers || {})
      };

      const config = {
        ...options,
        headers
      };
      
      const response = await fetch(endpoint, config);
      if (response.status === 401) {
        if (!window.location.pathname.startsWith('/login')) {
          window.location.href = '/login';
        }
        return { success: false, authenticated: false, error: 'Authentication required' };
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error || `Request failed with status ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.warn(`API Error on ${endpoint}:`, error.message);
      this.showToast(error.message, 'warning');
      throw error;
    }
  },

  // 1. Dashboard Overview
  async getDashboardOverview(lat = null, lon = null, city = null) {
    let url = `/api/dashboard/overview?visitor_id=${encodeURIComponent(this.getVisitorId())}`;
    if (lat !== null && lon !== null) {
      url += `&lat=${lat}&lon=${lon}`;
    }
    if (city) {
      url += `&city=${encodeURIComponent(city)}`;
    }
    return this.request(url);
  },

  // 2. City Geocoding Search
  async searchCities(query) {
    return this.request(`/api/dashboard/cities/search?q=${encodeURIComponent(query)}`);
  },

  // 3. PRANVYRA Intelligence Core AI Assistant
  async sendChatMessage(message, language = 'en', lat = null, lon = null, expertRole = 'auto') {
    return this.request('/api/assistant/chat', {
      method: 'POST',
      body: JSON.stringify({
        message,
        language,
        lat,
        lon,
        expert_role: expertRole,
        visitor_id: this.getVisitorId()
      })
    });
  },

  async getExperts() {
    return this.request('/api/assistant/experts');
  },

  async getChatHistory() {
    return this.request(`/api/assistant/history?visitor_id=${encodeURIComponent(this.getVisitorId())}`);
  },

  async clearChat() {
    return this.request('/api/assistant/clear', {
      method: 'POST',
      body: JSON.stringify({ visitor_id: this.getVisitorId() })
    });
  },

  // 4. Daily Planner
  async getDailyPlanner() {
    return this.request(`/api/planner/today?visitor_id=${encodeURIComponent(this.getVisitorId())}`);
  },

  async togglePlannerTask(taskId) {
    return this.request('/api/planner/toggle', {
      method: 'POST',
      body: JSON.stringify({ task_id: taskId, visitor_id: this.getVisitorId() })
    });
  },

  async regeneratePlanner() {
    return this.request('/api/planner/generate', {
      method: 'POST',
      body: JSON.stringify({ visitor_id: this.getVisitorId() })
    });
  },

  // 5. Indoor Air Check
  async submitIndoorCheck(formData) {
    return this.request('/api/indoor/check', {
      method: 'POST',
      body: JSON.stringify({ ...formData, visitor_id: this.getVisitorId() })
    });
  },

  async getLatestIndoorCheck() {
    return this.request(`/api/indoor/latest?visitor_id=${encodeURIComponent(this.getVisitorId())}`);
  },

  // 6. BreathRoute Journey Planner
  async planBreathRoute(origin, destination, departureTime = 'Now', preferredMode = 'public_transit', manualDistance = 12.0) {
    return this.request('/api/breath-route/plan', {
      method: 'POST',
      body: JSON.stringify({
        origin,
        destination,
        departure_time: departureTime,
        preferred_mode: preferredMode,
        manual_distance: manualDistance,
        visitor_id: this.getVisitorId()
      })
    });
  },

  async commitBreathRouteTrip(origin, destination, modeName, distanceKm, savingsKg) {
    return this.request('/api/breath-route/commit-trip', {
      method: 'POST',
      body: JSON.stringify({
        origin,
        destination,
        mode_name: modeName,
        distance_km: distanceKm,
        savings_kg: savingsKg,
        visitor_id: this.getVisitorId()
      })
    });
  },

  // 7. Life-Switch Environmental What-If Engine
  async getLifeSwitchCatalog() {
    return this.request('/api/life-switch/catalog');
  },

  async simulateLifeSwitch(switchKey, paramValue = null) {
    return this.request('/api/life-switch/simulate', {
      method: 'POST',
      body: JSON.stringify({
        switch_key: switchKey,
        param_value: paramValue
      })
    });
  },

  async commitLifeSwitch(switchKey, paramValue = null) {
    return this.request('/api/life-switch/commit', {
      method: 'POST',
      body: JSON.stringify({
        switch_key: switchKey,
        param_value: paramValue,
        visitor_id: this.getVisitorId()
      })
    });
  },

  // 8. Personal Impact Tracker & Receipts
  async getImpactSummary() {
    return this.request(`/api/impact/summary?visitor_id=${encodeURIComponent(this.getVisitorId())}`);
  },

  async getImpactReceipts() {
    return this.request(`/api/impact/receipts?visitor_id=${encodeURIComponent(this.getVisitorId())}`);
  },

  async getImpactHistory() {
    return this.request(`/api/impact/history?visitor_id=${encodeURIComponent(this.getVisitorId())}`);
  },

  async getAlternatives() {
    return this.request('/api/impact/alternatives');
  },

  async logImpactAction(actionData) {
    return this.request('/api/impact/log', {
      method: 'POST',
      body: JSON.stringify({ ...actionData, visitor_id: this.getVisitorId() })
    });
  },

  // 9. Neighborhood Pulse & Community Challenges
  async getNeighborhoodPulse() {
    return this.request('/api/community/pulse');
  },

  async getCommunityChallenges() {
    return this.request(`/api/community/challenges?visitor_id=${encodeURIComponent(this.getVisitorId())}`);
  },

  async joinChallenge(challengeId) {
    return this.request('/api/community/join', {
      method: 'POST',
      body: JSON.stringify({ challenge_id: challengeId, visitor_id: this.getVisitorId() })
    });
  },

  async updateChallengeProgress(challengeId, step = 35) {
    return this.request('/api/community/progress', {
      method: 'POST',
      body: JSON.stringify({ challenge_id: challengeId, increment_pct: step, visitor_id: this.getVisitorId() })
    });
  },

  // 10. Air-Twin & User Profiles
  async getAirTwin() {
    return this.request(`/api/user/air-twin?visitor_id=${encodeURIComponent(this.getVisitorId())}`);
  },

  async getUserProfile() {
    return this.request(`/api/user/profile?visitor_id=${encodeURIComponent(this.getVisitorId())}`);
  },

  async updateUserProfile(profileData) {
    return this.request('/api/user/profile', {
      method: 'PUT',
      body: JSON.stringify({ ...profileData, visitor_id: this.getVisitorId() })
    });
  },

  async registerOptionalAccount(email, username, password) {
    return this.request('/api/user/register', {
      method: 'POST',
      body: JSON.stringify({ email, username, password, visitor_id: this.getVisitorId() })
    });
  },

  async logout() {
    try {
      await fetch('/api/auth/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
    } catch (e) {}
    localStorage.removeItem('pranvyra_visitor_id');
    window.location.href = '/login';
  }
};
