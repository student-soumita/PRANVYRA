/**
 * PRANVYRA INTELLIGENCE CORE — Controller
 * Feature E: Multi-Role Environmental AI Assistant with Intent Routing,
 * Multi-Turn Conversational Memory, and Trilingual Intelligence.
 */
window.PranvyraAssistant = {
  currentLanguage: 'en',
  currentExpertRole: 'auto',
  expertMetadata: {},

  init() {
    this.currentLanguage = window.PranvyraState ? window.PranvyraState.language : (localStorage.getItem('pranvyra_lang') || 'en');
    this.bindEvents();
    this.loadExperts();
    this.loadHistory();

    // Listen for language change events
    window.addEventListener('pranvyra:language_changed', (e) => {
      this.currentLanguage = e.detail.language;
      this.updateLanguageContext();
    });
  },

  bindEvents() {
    const sendBtn = document.getElementById('chatSendBtn');
    const input = document.getElementById('chatInput');
    const clearBtn = document.getElementById('clearChatBtn');
    const roleSelect = document.getElementById('expertRoleSelect');

    if (sendBtn && input) {
      sendBtn.addEventListener('click', () => this.handleSendMessage());
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
          e.preventDefault();
          this.handleSendMessage();
        }
      });
    }

    if (roleSelect) {
      roleSelect.addEventListener('change', (e) => {
        this.currentExpertRole = e.target.value;
        this.updateActiveExpertIndicator();
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener('click', async () => {
        await window.PranvyraAPI.clearChat();
        const container = document.getElementById('chatMessages');
        if (container) container.innerHTML = '';
        this.appendAssistantWelcome();
        const msg = window.PranvyraI18n ? window.PranvyraI18n.t('ai_clear_btn', 'Cleared') : 'Cleared';
        window.PranvyraAPI.showToast('Conversation history reset.', 'info');
      });
    }

    // Quick starter prompt chips
    document.querySelectorAll('#chatQuickPromptsBar .prompt-chip').forEach(chip => {
      chip.addEventListener('click', (e) => {
        const promptText = e.currentTarget.textContent.trim();
        const input = document.getElementById('chatInput');
        if (input) {
          input.value = promptText;
          this.handleSendMessage();
        }
      });
    });
  },

  async loadExperts() {
    try {
      const res = await window.PranvyraAPI.getExperts();
      if (res.success && res.experts) {
        res.experts.forEach(exp => {
          this.expertMetadata[exp.id] = exp;
        });
      }
    } catch (e) {
      console.warn("Could not load expert metadata:", e);
    }
  },

  updateActiveExpertIndicator(primaryRole = null, isAuto = null) {
    const indicator = document.getElementById('activeExpertIndicator');
    const textEl = document.getElementById('activeExpertText');
    if (!indicator || !textEl) return;

    const roleToUse = primaryRole || this.currentExpertRole;
    
    if (roleToUse === 'auto') {
      textEl.textContent = this.getLocalizedText({
        en: 'Auto Expert Routing Active',
        hi: 'स्वचालित विशेषज्ञ चयन सक्रिय',
        bn: 'স্বয়ংক্রিয় বিশেষজ্ঞ নির্বাচন সক্রিয়'
      });
      indicator.className = 'active-expert-badge';
    } else {
      const exp = this.expertMetadata[roleToUse];
      let title = roleToUse.replace('_', ' ').toUpperCase();
      if (exp) {
        if (this.currentLanguage === 'hi' && exp.title_hi) title = exp.title_hi;
        else if (this.currentLanguage === 'bn' && exp.title_bn) title = exp.title_bn;
        else title = exp.title;
      }
      
      const prefix = isAuto ? this.getLocalizedText({
        en: 'Routed as: ',
        hi: 'सक्रिय विशेषज्ञ: ',
        bn: 'নির্বাচিত বিশেষজ্ঞ: '
      }) : '';

      textEl.textContent = `${prefix}${title}`;
      indicator.className = 'active-expert-badge active-specific';
    }

    if (window.lucide) window.lucide.createIcons();
  },

  updateLanguageContext() {
    const input = document.getElementById('chatInput');
    if (input && window.PranvyraI18n) {
      input.placeholder = window.PranvyraI18n.t('ai_input_placeholder', input.placeholder);
    }
    this.updateActiveExpertIndicator();
  },

  getLocalizedText(map) {
    return map[this.currentLanguage] || map.en || '';
  },

  async loadHistory() {
    try {
      const res = await window.PranvyraAPI.getChatHistory();
      if (res && res.history && res.history.length > 0) {
        const container = document.getElementById('chatMessages');
        if (!container) return;
        container.innerHTML = '';
        res.history.forEach(item => {
          if (item.role === 'user') {
            this.appendUserMessage(item.message);
          } else {
            let card = item.structured_card;
            if (typeof card === 'string') {
              try { card = JSON.parse(card); } catch (e) { card = null; }
            }
            this.appendAssistantMessage({
              text: item.message,
              structuredCard: card,
              expertTitle: 'PRANVYRA Intelligence'
            });
          }
        });
        container.scrollTop = container.scrollHeight;
      } else {
        this.appendAssistantWelcome();
      }
    } catch (e) {
      console.warn("Could not load chat history:", e);
      this.appendAssistantWelcome();
    }
  },

  appendAssistantWelcome() {
    const welcomeMap = {
      en: "Welcome to PRANVYRA Intelligence Core! I synthesize the reasoning of five specialized environmental experts: Atmospheric Scientist, Urban Mobility Expert, Indoor Air Specialist, Sustainability Strategist, and Environmental Research Analyst. Ask me anything about your local air, cleaner commuting, indoor ventilation, carbon reduction, or scientific datasets.",
      hi: "प्राणवायरा इंटेलिजेंस कोर (PRANVYRA Intelligence Core) में आपका स्वागत है! मैं पांच पर्यावरण विशेषज्ञों के दृष्टिकोण को एकीकृत करता हूँ: वायुमंडलीय वैज्ञानिक, शहरी गतिशीलता विशेषज्ञ, घर की वायु विशेषज्ञ, स्थिरता रणनीतिकार, और पर्यावरण अनुसंधान विश्लेषक। स्थानीय वायु गुणवत्ता, स्वच्छ यात्रा, वेंटिलेशन या कार्बन कमी पर कोई भी प्रश्न पूछें।",
      bn: "প্রাণবায়রা ইন্টেলিজেন্স কোর (PRANVYRA Intelligence Core)-এ স্বাগতম! আমি পাঁচজন পরিবেশ বিশেষজ্ঞের দৃষ্টিভঙ্গি সমন্বয় করি: বায়ুমণ্ডলীয় বিজ্ঞানী, নগর গতিশীলতা বিশেষজ্ঞ, ঘরের অভ্যন্তরীণ বায়ু বিশেষজ্ঞ, স্থায়িত্ব কৌশলবিদ, এবং পরিবেশ গবেষণা বিশ্লেষক। বায়ুমান, যাতায়াত, ঘরের বাতাস বা কার্বন হ্রাস নিয়ে যেকোনো প্রশ্ন জিজ্ঞাসা করুন।"
    };

    this.appendAssistantMessage({
      text: this.getLocalizedText(welcomeMap),
      structuredCard: {
        problem_identified: "Ambient boundary layer inversions and urban commuting dynamics create fluctuating local exposure.",
        recommended_action: "Review today's AirWise action and plan low-emission commuting using BreathRoute.",
        reason: "Boundary layer thermal dynamics trap morning surface exhaust plumes near ground level.",
        expected_benefit: "Protects respiratory health while eliminating avoidable daily carbon emissions.",
        estimated_impact: "Avoids 1.5 – 3.5 kg CO₂e per daily commute journey.",
        confidence_level: "High (95%)",
        source: "Copernicus CAMS & UK DEFRA 2023 Factors"
      },
      expertTitle: "PRANVYRA Intelligence Core",
      followUps: [
        this.getLocalizedText({
          en: "Analyze my local air quality and weather.",
          hi: "मेरी स्थानीय हवा और मौसम का वैज्ञानिक विश्लेषण करें।",
          bn: "আমার এলাকার বাতাস ও আবহাওয়ার বৈজ্ঞানিক বিশ্লেষণ দিন।"
        }),
        this.getLocalizedText({
          en: "Find a cleaner commute option for today.",
          hi: "आज के सफर के लिए स्वच्छ यात्रा विकल्प खोजें।",
          bn: "আজকের যাতায়াতের জন্য পরিবেশবান্ধব বিকল্প খুঁজুন।"
        }),
        this.getLocalizedText({
          en: "How can I improve my indoor air when cooking?",
          hi: "खाना बनाते समय घर की हवा कैसे सुधारें?",
          bn: "রান্নার সময় ঘরের বাতাস কীভাবে ভালো রাখব?"
        })
      ]
    });
  },

  async handleSendMessage() {
    const input = document.getElementById('chatInput');
    if (!input) return;

    const message = input.value.trim();
    if (!message) return;

    input.value = '';
    this.appendUserMessage(message);

    const typing = document.getElementById('chatTypingIndicator');
    if (typing) typing.style.display = 'flex';

    const container = document.getElementById('chatMessages');
    if (container) container.scrollTop = container.scrollHeight;

    try {
      const lat = window.PranvyraState ? window.PranvyraState.profile.latitude : null;
      const lon = window.PranvyraState ? window.PranvyraState.profile.longitude : null;
      
      const res = await window.PranvyraAPI.sendChatMessage(
        message,
        this.currentLanguage,
        lat,
        lon,
        this.currentExpertRole
      );

      if (typing) typing.style.display = 'none';

      if (res.success) {
        // Update active expert indicator based on routing result
        this.updateActiveExpertIndicator(res.primary_role, res.is_auto_routed);

        this.appendAssistantMessage({
          text: res.reply,
          structuredCard: res.structured_card,
          expertTitle: res.expert_title,
          primaryRole: res.primary_role,
          multiRoles: res.multi_expert_roles,
          routingReason: res.routing_reason,
          followUps: res.follow_up_suggestions
        });
      }
    } catch (error) {
      if (typing) typing.style.display = 'none';
      const fallbackText = this.getLocalizedText({
        en: "I experienced an issue connecting to live telemetry. Based on general atmospheric science: verify outdoor AQI before aerobic workouts, ensure continuous kitchen exhaust during cooking, and consider electric transit to avoid direct tailpipe inhalation.",
        hi: "लाइव डेटा कनेक्शन में बाधा आई। सामान्य वैज्ञानिक दिशानिर्देश: तीव्र व्यायाम से पहले AQI जांचें, खाना बनाते समय एग्जॉस्ट चलाएं, और साइलेंसर के धुएं से बचने के लिए मेट्रो का उपयोग करें।",
        bn: "লাইভ তথ্য সংযোগে সমস্যা হয়েছে। সাধারণ বৈজ্ঞানিক পরামর্শ: ব্যায়ামের আগে AQI পরীক্ষা করুন, রান্নার সময় এক্সহস্ট চালু রাখুন এবং মেট্রো ব্যবহার করুন।"
      });
      this.appendAssistantMessage({
        text: fallbackText,
        expertTitle: "Environmental Research Analyst"
      });
    }

    if (container) container.scrollTop = container.scrollHeight;
  },

  appendUserMessage(text) {
    const container = document.getElementById('chatMessages');
    if (!container) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message message-user';
    msgDiv.innerHTML = `
      <div class="msg-avatar"><i data-lucide="user"></i></div>
      <div class="msg-bubble"><p>${this.escapeHtml(text)}</p></div>
    `;
    container.appendChild(msgDiv);
    if (window.lucide) window.lucide.createIcons({ root: msgDiv });
    container.scrollTop = container.scrollHeight;
  },

  appendAssistantMessage({ text, structuredCard, expertTitle, primaryRole, multiRoles, routingReason, followUps }) {
    const container = document.getElementById('chatMessages');
    if (!container) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message message-assistant';

    // Expert Header Tag
    let expertTagHtml = '';
    if (expertTitle) {
      expertTagHtml = `
        <div class="msg-expert-tag">
          <i data-lucide="cpu"></i>
          <span>${this.escapeHtml(expertTitle)}</span>
        </div>
      `;
    }

    // Structured Advice Card
    let cardHtml = '';
    if (structuredCard) {
      const actionTitle = structuredCard.recommended_action || structuredCard.next_best_action || 'Actionable Recommendation';
      cardHtml = `
        <div class="structured-advice-card">
          <div class="card-tag">PRANVYRA ADVICE BLUEPRINT</div>
          <h4 class="advice-title">${this.escapeHtml(actionTitle)}</h4>
          
          <div class="advice-field">
            <span class="advice-label">Problem Identified:</span>
            <span class="advice-text">${this.escapeHtml(structuredCard.problem_identified || structuredCard.issue || '')}</span>
          </div>
          
          <div class="advice-field">
            <span class="advice-label">Scientific Reason:</span>
            <span class="advice-text">${this.escapeHtml(structuredCard.reason || structuredCard.importance || '')}</span>
          </div>

          <div class="advice-field">
            <span class="advice-label">Expected Benefit:</span>
            <span class="advice-text">${this.escapeHtml(structuredCard.expected_benefit || structuredCard.benefit || '')}</span>
          </div>

          <div class="advice-field">
            <span class="advice-label">Estimated Impact:</span>
            <span class="advice-text">${this.escapeHtml(structuredCard.estimated_impact || structuredCard.assumptions || '')}</span>
          </div>

          <div class="advice-meta-row">
            <span class="advice-conf"><i data-lucide="check-circle-2"></i> ${this.escapeHtml(structuredCard.confidence_level || structuredCard.confidence || 'High (90%)')}</span>
            <span class="advice-src"><i data-lucide="database"></i> ${this.escapeHtml(structuredCard.source || 'US EPA / DEFRA')}</span>
          </div>
        </div>
      `;
    }

    // Action Highlight Banner
    let actionBanner = '';
    if (structuredCard && (structuredCard.recommended_action || structuredCard.next_best_action)) {
      const act = structuredCard.recommended_action || structuredCard.next_best_action;
      actionBanner = `
        <div class="next-best-action-banner">
          <i data-lucide="zap"></i>
          <strong>YOUR NEXT BEST ACTION:</strong> ${this.escapeHtml(act)}
        </div>
      `;
    }

    // Follow-up Suggestions
    let followUpsHtml = '';
    if (followUps && followUps.length > 0) {
      const chips = followUps.map(fu => `<button class="followup-chip">${this.escapeHtml(fu)}</button>`).join('');
      followUpsHtml = `
        <div class="followup-suggestions-box">
          <span class="followup-label">${this.getLocalizedText({ en: 'Suggested Follow-ups:', hi: 'सुझाए गए अगले प्रश्न:', bn: 'সম্পর্কিত প্রশ্ন:' })}</span>
          <div class="followup-chips-row">${chips}</div>
        </div>
      `;
    }

    // Format Markdown paragraphs & bold text
    const formattedParagraphs = (text || '').split('\n\n').map(p => {
      let html = this.escapeHtml(p);
      html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
      return `<p>${html}</p>`;
    }).join('');

    msgDiv.innerHTML = `
      <div class="msg-avatar"><img src="/static/assets/logo.svg" alt="PRANVYRA"></div>
      <div class="msg-bubble">
        ${expertTagHtml}
        ${formattedParagraphs}
        ${cardHtml}
        ${actionBanner}
        ${followUpsHtml}
      </div>
    `;

    // Bind follow-up clicks
    msgDiv.querySelectorAll('.followup-chip').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const query = e.target.textContent.trim();
        const input = document.getElementById('chatInput');
        if (input) {
          input.value = query;
          this.handleSendMessage();
        }
      });
    });

    container.appendChild(msgDiv);
    if (window.lucide) window.lucide.createIcons({ root: msgDiv });
    container.scrollTop = container.scrollHeight;
  },

  escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
};

document.addEventListener('DOMContentLoaded', () => {
  window.PranvyraAssistant.init();
});
