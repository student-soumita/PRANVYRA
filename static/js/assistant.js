/**
 * PRANVYRA INTELLIGENCE CORE — Controller
 * Feature E: Multi-Role Environmental AI Assistant with Intent Routing,
 * Multi-Turn Conversational Memory, and Trilingual Voice AI Companion (EN-IN, HI-IN, BN-IN).
 * Tagline: Every Breath. A Better Tomorrow.
 */
window.PranvyraAssistant = {
  currentLanguage: 'en',
  currentExpertRole: 'auto',
  expertMetadata: {},

  // Voice Interaction State
  isRecording: false,
  isSpeaking: false,
  isPaused: false,
  autoReadEnabled: false,
  recognition: null,
  currentUtterance: null,
  availableVoices: [],
  activeSpeakingBtn: null,

  init() {
    this.currentLanguage = window.PranvyraState ? window.PranvyraState.language : (localStorage.getItem('pranvyra_lang') || 'en');
    this.bindEvents();
    this.initVoice();
    this.loadExperts();
    this.loadHistory();

    // Listen for language change events
    window.addEventListener('pranvyra:language_changed', (e) => {
      this.currentLanguage = e.detail.language;
      this.handleLanguageChanged();
    });

    // Global Stop All Speech button
    const stopAllBtn = document.getElementById('chatStopAllSpeechBtn');
    if (stopAllBtn) {
      stopAllBtn.addEventListener('click', () => this.stopSpeech());
    }
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
        this.stopSpeech();
        this.stopVoiceInput();
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

  // ===================================================================
  // TRILINGUAL VOICE SYSTEM: INPUT (STT) & OUTPUT (TTS)
  // ===================================================================
  initVoice() {
    // 1. Initialize voices list for SpeechSynthesis
    if ('speechSynthesis' in window) {
      this.loadVoices();
      window.speechSynthesis.onvoiceschanged = () => this.loadVoices();
    }

    // 2. Load auto-read preference
    this.autoReadEnabled = localStorage.getItem('pranvyra_autoread') === 'true';
    this.updateAutoSpeechButtonUI();

    // 3. Microphone Button (Voice Input)
    const micBtn = document.getElementById('chatVoiceInputBtn');
    if (micBtn) {
      micBtn.addEventListener('click', () => this.toggleVoiceInput());
    }

    // 4. Auto-Speech Toggle in Chat Header
    const autoSpeechBtn = document.getElementById('chatAutoSpeechToggle');
    if (autoSpeechBtn) {
      autoSpeechBtn.addEventListener('click', () => this.toggleAutoRead());
    }

    // 5. Speech Control Bar actions
    const stopListeningBtn = document.getElementById('voiceStopListeningBtn');
    if (stopListeningBtn) {
      stopListeningBtn.addEventListener('click', () => this.stopVoiceInput());
    }

    const pauseResumeBtn = document.getElementById('voicePauseResumeBtn');
    if (pauseResumeBtn) {
      pauseResumeBtn.addEventListener('click', () => this.togglePauseResumeSpeech());
    }

    const stopSpeakingBtn = document.getElementById('voiceStopSpeakingBtn');
    if (stopSpeakingBtn) {
      stopSpeakingBtn.addEventListener('click', () => this.stopSpeech());
    }
  },

  loadVoices() {
    if ('speechSynthesis' in window) {
      this.availableVoices = window.speechSynthesis.getVoices() || [];
    }
  },

  getRecognitionLocale() {
    switch (this.currentLanguage) {
      case 'hi':
        return 'hi-IN';
      case 'bn':
        return 'bn-IN';
      case 'en':
      default:
        return 'en-IN';
    }
  },

  toggleVoiceInput() {
    if (this.isRecording) {
      this.stopVoiceInput();
    } else {
      this.startVoiceInput();
    }
  },

  startVoiceInput() {
    // Stop any speech playing before listening
    this.stopSpeech();

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      const msg = window.PranvyraI18n 
        ? window.PranvyraI18n.t('speech_recognition_unsupported', 'Speech recognition is not supported in this browser.')
        : 'Speech recognition is not supported in this browser. Please use Chrome or Edge.';
      if (window.PranvyraAPI && window.PranvyraAPI.showToast) {
        window.PranvyraAPI.showToast(msg, 'warning');
      } else {
        alert(msg);
      }
      return;
    }

    // Prevent multiple sessions
    if (this.recognition) {
      try { this.recognition.abort(); } catch (e) {}
      this.recognition = null;
    }

    try {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = true;
      this.recognition.maxAlternatives = 1;
      this.recognition.lang = this.getRecognitionLocale();

      const input = document.getElementById('chatInput');
      const micBtn = document.getElementById('chatVoiceInputBtn');
      const statusBar = document.getElementById('voiceStatusBar');
      const statusText = document.getElementById('voiceStatusText');
      const stopListeningBtn = document.getElementById('voiceStopListeningBtn');
      const pauseResumeBtn = document.getElementById('voicePauseResumeBtn');
      const stopSpeakingBtn = document.getElementById('voiceStopSpeakingBtn');

      let initialInputValue = input ? input.value : '';

      this.recognition.onstart = () => {
        this.isRecording = true;
        if (micBtn) {
          micBtn.classList.add('listening');
          const stopTitle = window.PranvyraI18n ? window.PranvyraI18n.t('stop_listening', 'Stop Listening') : 'Stop Listening';
          micBtn.setAttribute('title', stopTitle);
          micBtn.setAttribute('aria-label', stopTitle);
        }

        if (statusBar) {
          statusBar.className = 'voice-status-bar listening';
          statusBar.style.display = 'flex';
        }

        if (statusText) {
          statusText.textContent = window.PranvyraI18n ? window.PranvyraI18n.t('listening', 'Listening...') : 'Listening...';
        }

        if (stopListeningBtn) stopListeningBtn.style.display = 'inline-flex';
        if (pauseResumeBtn) pauseResumeBtn.style.display = 'none';
        if (stopSpeakingBtn) stopSpeakingBtn.style.display = 'none';

        if (input) input.focus();
        if (window.lucide) window.lucide.createIcons();
      };

      this.recognition.onresult = (event) => {
        let interimTranscript = '';
        let finalTranscript = '';

        for (let i = event.resultIndex; i < event.results.length; ++i) {
          const item = event.results[i];
          if (item.isFinal) {
            finalTranscript += item[0].transcript;
          } else {
            interimTranscript += item[0].transcript;
          }
        }

        const currentText = finalTranscript || interimTranscript;
        if (input && currentText) {
          const prefix = initialInputValue ? `${initialInputValue.trim()} ` : '';
          input.value = prefix + currentText;
        }

        if (statusText && (interimTranscript || finalTranscript)) {
          const prefix = window.PranvyraI18n ? window.PranvyraI18n.t('processing_voice', 'Processing...') : 'Processing...';
          statusText.textContent = `${prefix} "${currentText.slice(0, 36)}${currentText.length > 36 ? '...' : ''}"`;
        }
      };

      this.recognition.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
        let errorMsg = '';
        
        switch (event.error) {
          case 'not-allowed':
          case 'service-not-allowed':
            errorMsg = window.PranvyraI18n ? window.PranvyraI18n.t('microphone_permission_denied') : 'Microphone access denied.';
            break;
          case 'audio-capture':
            errorMsg = window.PranvyraI18n ? window.PranvyraI18n.t('microphone_not_found') : 'No microphone detected.';
            break;
          case 'network':
            errorMsg = window.PranvyraI18n ? window.PranvyraI18n.t('voice_input_error') : 'Network error during voice recognition.';
            break;
          case 'no-speech':
            // No speech detected, quietly finish
            break;
          default:
            errorMsg = window.PranvyraI18n ? window.PranvyraI18n.t('voice_input_error') : 'Voice recognition error.';
        }

        if (errorMsg && window.PranvyraAPI && window.PranvyraAPI.showToast) {
          window.PranvyraAPI.showToast(errorMsg, 'warning');
        }

        this.cleanupVoiceInputUI();
      };

      this.recognition.onend = () => {
        this.cleanupVoiceInputUI();
      };

      this.recognition.start();
    } catch (err) {
      console.warn('Could not start speech recognition:', err);
      this.cleanupVoiceInputUI();
    }
  },

  stopVoiceInput() {
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {
        try { this.recognition.abort(); } catch (e2) {}
      }
    }
    this.cleanupVoiceInputUI();
  },

  cleanupVoiceInputUI() {
    this.isRecording = false;
    this.recognition = null;

    const micBtn = document.getElementById('chatVoiceInputBtn');
    if (micBtn) {
      micBtn.classList.remove('listening');
      const startTitle = window.PranvyraI18n ? window.PranvyraI18n.t('start_listening', 'Start Voice Input') : 'Start Voice Input';
      micBtn.setAttribute('title', startTitle);
      micBtn.setAttribute('aria-label', startTitle);
    }

    const stopListeningBtn = document.getElementById('voiceStopListeningBtn');
    if (stopListeningBtn) stopListeningBtn.style.display = 'none';

    // If not currently speaking, hide the voice status bar
    if (!this.isSpeaking) {
      const statusBar = document.getElementById('voiceStatusBar');
      if (statusBar) statusBar.style.display = 'none';
    }

    if (window.lucide) window.lucide.createIcons();
  },

  // -------------------------------------------------------------------
  // SPEECH SYNTHESIS (VOICE OUTPUT)
  // -------------------------------------------------------------------
  getBestVoiceForCurrentLanguage() {
    this.loadVoices();
    const voices = this.availableVoices || [];
    const lang = this.currentLanguage;

    if (lang === 'hi') {
      // Find native Hindi voice
      const hiVoice = voices.find(v => {
        const vl = (v.lang || '').toLowerCase().replace('_', '-');
        return vl.startsWith('hi') || (v.name && v.name.toLowerCase().includes('hindi'));
      });
      return hiVoice || null;
    } else if (lang === 'bn') {
      // Find native Bengali voice
      const bnVoice = voices.find(v => {
        const vl = (v.lang || '').toLowerCase().replace('_', '-');
        return vl.startsWith('bn') || (v.name && (v.name.toLowerCase().includes('bengali') || v.name.toLowerCase().includes('bangla')));
      });
      return bnVoice || null;
    } else {
      // English: prefer en-IN, then en-US, en-GB, en
      const enInVoice = voices.find(v => {
        const vl = (v.lang || '').toLowerCase().replace('_', '-');
        return vl === 'en-in' || vl.startsWith('en-in');
      });
      if (enInVoice) return enInVoice;

      const enUsVoice = voices.find(v => {
        const vl = (v.lang || '').toLowerCase().replace('_', '-');
        return vl === 'en-us' || vl.startsWith('en-us');
      });
      if (enUsVoice) return enUsVoice;

      const anyEnVoice = voices.find(v => (v.lang || '').toLowerCase().startsWith('en'));
      return anyEnVoice || (voices.length > 0 ? voices[0] : null);
    }
  },

  cleanTextForSpeech(text) {
    if (!text) return '';
    let cleaned = text;
    // Remove code blocks
    cleaned = cleaned.replace(/```[\s\S]*?```/g, '');
    // Remove inline code
    cleaned = cleaned.replace(/`([^`]+)`/g, '$1');
    // Remove markdown links [text](url) -> text
    cleaned = cleaned.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1');
    // Remove bold and italics
    cleaned = cleaned.replace(/(\*\*|\*|__|_)(.*?)\1/g, '$2');
    // Remove markdown headings (# Heading)
    cleaned = cleaned.replace(/^#+\s+/gm, '');
    // Remove blockquotes and bullet points
    cleaned = cleaned.replace(/^>\s+/gm, '');
    cleaned = cleaned.replace(/^[\*\-]\s+/gm, '');
    // Remove HTML tags
    cleaned = cleaned.replace(/<[^>]*>/g, '');
    // Clean excessive whitespaces and newlines
    cleaned = cleaned.replace(/\s+/g, ' ').trim();
    return cleaned;
  },

  speakText(rawText, messageBtn = null) {
    if (!('speechSynthesis' in window)) {
      const msg = window.PranvyraI18n 
        ? window.PranvyraI18n.t('speech_synthesis_unsupported', 'Speech synthesis is not supported in this browser.')
        : 'Speech synthesis is not supported in this browser.';
      if (window.PranvyraAPI && window.PranvyraAPI.showToast) {
        window.PranvyraAPI.showToast(msg, 'warning');
      }
      return;
    }

    // Stop any ongoing speech first (prevents overlapping)
    this.stopSpeech();

    const voice = this.getBestVoiceForCurrentLanguage();
    // CRITICAL: If Hindi or Bengali voice is unavailable, do NOT speak with an English voice!
    if (!voice && (this.currentLanguage === 'hi' || this.currentLanguage === 'bn')) {
      const msg = window.PranvyraI18n 
        ? window.PranvyraI18n.t('language_voice_unavailable', 'Natural voice for this language is currently unavailable on your system. Displaying text response.')
        : 'Natural voice for this language is currently unavailable on your system. Displaying text response.';
      if (window.PranvyraAPI && window.PranvyraAPI.showToast) {
        window.PranvyraAPI.showToast(msg, 'warning');
      }
      // Disable play button for this message
      if (messageBtn) {
        messageBtn.disabled = true;
        messageBtn.setAttribute('title', msg);
      }
      return;
    }

    const cleanText = this.cleanTextForSpeech(rawText);
    if (!cleanText) return;

    try {
      const utterance = new SpeechSynthesisUtterance(cleanText);
      if (voice) {
        utterance.voice = voice;
        utterance.lang = voice.lang;
      } else {
        utterance.lang = this.getRecognitionLocale();
      }
      utterance.rate = 0.95; // Clear and measured pace
      utterance.pitch = 1.0;

      const statusBar = document.getElementById('voiceStatusBar');
      const statusText = document.getElementById('voiceStatusText');
      const pauseResumeBtn = document.getElementById('voicePauseResumeBtn');
      const pauseResumeIcon = document.getElementById('voicePauseResumeIcon');
      const stopSpeakingBtn = document.getElementById('voiceStopSpeakingBtn');
      const stopListeningBtn = document.getElementById('voiceStopListeningBtn');
      const globalStopBtn = document.getElementById('chatStopAllSpeechBtn');

      // Find the per-message controls container
      const msgContainer = messageBtn ? messageBtn.closest('.chat-message') : null;

      utterance.onstart = () => {
        this.isSpeaking = true;
        this.isPaused = false;
        this.currentUtterance = utterance;

        // Update per-message button states
        if (messageBtn) {
          messageBtn.classList.add('active');
          this.activeSpeakingBtn = messageBtn;
        }

        // Update per-message control visibility
        if (msgContainer) {
          this.setMsgControlState(msgContainer, 'playing');
        }

        // Show global stop button
        if (globalStopBtn) globalStopBtn.style.display = 'inline-flex';

        if (statusBar) {
          statusBar.className = 'voice-status-bar speaking';
          statusBar.style.display = 'flex';
        }

        if (statusText) {
          statusText.textContent = window.PranvyraI18n ? window.PranvyraI18n.t('speaking', 'Speaking AI Response...') : 'Speaking AI Response...';
        }

        if (pauseResumeBtn) pauseResumeBtn.style.display = 'inline-flex';
        if (pauseResumeIcon) pauseResumeIcon.setAttribute('data-lucide', 'pause');
        if (stopSpeakingBtn) stopSpeakingBtn.style.display = 'inline-flex';
        if (stopListeningBtn) stopListeningBtn.style.display = 'none';

        if (window.lucide) window.lucide.createIcons();
      };

      utterance.onpause = () => {
        this.isPaused = true;
        if (pauseResumeIcon) pauseResumeIcon.setAttribute('data-lucide', 'play');
        if (statusText) {
          statusText.textContent = window.PranvyraI18n ? window.PranvyraI18n.t('speech_paused', 'Speech paused.') : 'Speech paused.';
        }
        if (msgContainer) {
          this.setMsgControlState(msgContainer, 'paused');
        }
        if (window.lucide) window.lucide.createIcons();
      };

      utterance.onresume = () => {
        this.isPaused = false;
        if (pauseResumeIcon) pauseResumeIcon.setAttribute('data-lucide', 'pause');
        if (statusText) {
          statusText.textContent = window.PranvyraI18n ? window.PranvyraI18n.t('speaking', 'Speaking AI Response...') : 'Speaking AI Response...';
        }
        if (msgContainer) {
          this.setMsgControlState(msgContainer, 'playing');
        }
        if (window.lucide) window.lucide.createIcons();
      };

      utterance.onend = () => {
        if (msgContainer) {
          this.setMsgControlState(msgContainer, 'idle');
        }
        this.cleanupSpeechUI();
      };

      utterance.onerror = (e) => {
        console.warn('SpeechSynthesis error:', e);
        if (msgContainer) {
          this.setMsgControlState(msgContainer, 'idle');
        }
        this.cleanupSpeechUI();
      };

      window.speechSynthesis.speak(utterance);
    } catch (e) {
      console.warn('Could not play speech:', e);
      this.cleanupSpeechUI();
    }
  },

  togglePauseResumeSpeech() {
    if (!('speechSynthesis' in window) || !this.isSpeaking) return;

    if (window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
      this.isPaused = false;
      const icon = document.getElementById('voicePauseResumeIcon');
      if (icon) icon.setAttribute('data-lucide', 'pause');
    } else if (window.speechSynthesis.speaking) {
      window.speechSynthesis.pause();
      this.isPaused = true;
      const icon = document.getElementById('voicePauseResumeIcon');
      if (icon) icon.setAttribute('data-lucide', 'play');
    }
    if (window.lucide) window.lucide.createIcons();
  },

  stopSpeech() {
    if ('speechSynthesis' in window) {
      try {
        window.speechSynthesis.cancel();
      } catch (e) {}
    }
    this.cleanupSpeechUI();
  },

  cleanupSpeechUI() {
    this.isSpeaking = false;
    this.isPaused = false;
    this.currentUtterance = null;

    if (this.activeSpeakingBtn) {
      this.activeSpeakingBtn.classList.remove('active');
      // Reset per-message controls for the active message
      const msgContainer = this.activeSpeakingBtn.closest('.chat-message');
      if (msgContainer) {
        this.setMsgControlState(msgContainer, 'idle');
      }
      this.activeSpeakingBtn = null;
    }

    const pauseResumeBtn = document.getElementById('voicePauseResumeBtn');
    const stopSpeakingBtn = document.getElementById('voiceStopSpeakingBtn');
    const globalStopBtn = document.getElementById('chatStopAllSpeechBtn');
    if (pauseResumeBtn) pauseResumeBtn.style.display = 'none';
    if (stopSpeakingBtn) stopSpeakingBtn.style.display = 'none';
    if (globalStopBtn) globalStopBtn.style.display = 'none';

    // If not currently recording, hide the voice status bar
    if (!this.isRecording) {
      const statusBar = document.getElementById('voiceStatusBar');
      if (statusBar) statusBar.style.display = 'none';
    }

    if (window.lucide) window.lucide.createIcons();
  },

  /**
   * Updates per-message speech control button visibility and state.
   * States: 'idle', 'playing', 'paused'
   */
  setMsgControlState(msgContainer, state) {
    if (!msgContainer) return;
    const playBtn = msgContainer.querySelector('.btn-play-msg');
    const stopBtn = msgContainer.querySelector('.btn-stop-msg');
    const pauseBtn = msgContainer.querySelector('.btn-pause-msg');
    const resumeBtn = msgContainer.querySelector('.btn-resume-msg');
    const speakIndicator = msgContainer.querySelector('.msg-speaking-indicator');

    if (state === 'playing') {
      if (playBtn) playBtn.style.display = 'none';
      if (stopBtn) { stopBtn.style.display = 'inline-flex'; stopBtn.disabled = false; }
      if (pauseBtn) pauseBtn.style.display = 'inline-flex';
      if (resumeBtn) resumeBtn.style.display = 'none';
      if (speakIndicator) speakIndicator.style.display = 'inline-flex';
    } else if (state === 'paused') {
      if (playBtn) playBtn.style.display = 'none';
      if (stopBtn) { stopBtn.style.display = 'inline-flex'; stopBtn.disabled = false; }
      if (pauseBtn) pauseBtn.style.display = 'none';
      if (resumeBtn) resumeBtn.style.display = 'inline-flex';
      if (speakIndicator) speakIndicator.style.display = 'none';
    } else {
      // idle
      if (playBtn) playBtn.style.display = 'inline-flex';
      if (stopBtn) { stopBtn.style.display = 'inline-flex'; stopBtn.disabled = true; }
      if (pauseBtn) pauseBtn.style.display = 'none';
      if (resumeBtn) resumeBtn.style.display = 'none';
      if (speakIndicator) speakIndicator.style.display = 'none';
    }

    if (window.lucide) window.lucide.createIcons({ root: msgContainer });
  },

  toggleAutoRead() {
    this.autoReadEnabled = !this.autoReadEnabled;
    localStorage.setItem('pranvyra_autoread', this.autoReadEnabled);
    this.updateAutoSpeechButtonUI();

    const toastMsg = this.autoReadEnabled
      ? (window.PranvyraI18n ? window.PranvyraI18n.t('voice_auto_read_toggle') : 'Auto-read enabled.')
      : (window.PranvyraI18n ? window.PranvyraI18n.t('stop_speech') : 'Auto-read disabled.');
    if (window.PranvyraAPI && window.PranvyraAPI.showToast) {
      window.PranvyraAPI.showToast(toastMsg, 'info');
    }
  },

  updateAutoSpeechButtonUI() {
    const btn = document.getElementById('chatAutoSpeechToggle');
    if (btn) {
      btn.classList.toggle('active', this.autoReadEnabled);
      btn.setAttribute('aria-pressed', this.autoReadEnabled ? 'true' : 'false');
    }
  },

  handleLanguageChanged() {
    // 1. If currently recording or speaking, stop cleanly
    if (this.isRecording) this.stopVoiceInput();
    if (this.isSpeaking) this.stopSpeech();

    // 2. Update placeholders and expert indicators
    this.updateLanguageContext();

    // 3. Update tooltips and buttons
    const micBtn = document.getElementById('chatVoiceInputBtn');
    if (micBtn) {
      const title = window.PranvyraI18n ? window.PranvyraI18n.t('start_listening', 'Start Voice Input') : 'Start Voice Input';
      micBtn.setAttribute('title', title);
      micBtn.setAttribute('aria-label', title);
    }
  },

  // ===================================================================
  // EXPERT METADATA & REASONING
  // ===================================================================
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

  // ===================================================================
  // CONVERSATION HISTORY
  // ===================================================================
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
              expertTitle: 'PRANVYRA Intelligence',
              suppressAutoRead: true // Never auto-read past history
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
      suppressAutoRead: true, // Do not auto-read initial welcome
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

  // ===================================================================
  // MESSAGE SENDING & HANDLING
  // ===================================================================
  async handleSendMessage() {
    const input = document.getElementById('chatInput');
    if (!input) return;

    const message = input.value.trim();
    if (!message) return; // Do not send empty messages

    input.value = '';
    this.appendUserMessage(message);

    const typing = document.getElementById('chatTypingIndicator');
    if (typing) typing.style.display = 'flex';

    const container = document.getElementById('chatMessages');
    if (container) container.scrollTop = container.scrollHeight;

    try {
      const lat = window.PranvyraState ? window.PranvyraState.profile.latitude : null;
      const lon = window.PranvyraState ? window.PranvyraState.profile.longitude : null;
      
      const activeLang = (window.PranvyraI18n && window.PranvyraI18n.currentLanguage) ||
                         localStorage.getItem('pranvyra_lang') ||
                         this.currentLanguage || 'en';
      this.currentLanguage = activeLang;

      const res = await window.PranvyraAPI.sendChatMessage(
        message,
        activeLang,
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
          followUps: res.follow_up_suggestions,
          suppressAutoRead: false,
          wasTranslated: res.was_translated || false,
          translationFailed: res.translation_failed || false
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
        expertTitle: "Environmental Research Analyst",
        suppressAutoRead: false
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

  appendAssistantMessage({ text, structuredCard, expertTitle, primaryRole, multiRoles, routingReason, followUps, suppressAutoRead = false, wasTranslated = false, translationFailed = false }) {
    const container = document.getElementById('chatMessages');
    if (!container) return;

    const msgDiv = document.createElement('div');
    msgDiv.className = 'chat-message message-assistant';

    // Expert Header Tag & Per-Message Speech Controls Row
    const t = (key, fb) => window.PranvyraI18n ? window.PranvyraI18n.t(key, fb) : fb;
    const playTitle = t('play_response', 'Play Response');
    const stopTitle = t('stop_speaking', 'Stop Speaking');
    const pauseTitle = t('pause_speaking', 'Pause');
    const resumeTitle = t('resume_speaking', 'Resume');

    let expertHeaderRowHtml = `
      <div class="msg-expert-tag-row">
        <div class="msg-expert-tag">
          <i data-lucide="cpu"></i>
          <span>${this.escapeHtml(expertTitle || 'PRANVYRA Intelligence')}</span>
        </div>
        <div class="msg-speech-controls">
          <span class="msg-speaking-indicator" style="display:none;" aria-hidden="true">
            <span class="mini-wave-bar"></span><span class="mini-wave-bar"></span><span class="mini-wave-bar"></span>
          </span>
          <button class="btn-msg-ctrl btn-play-msg" type="button" title="${playTitle}" aria-label="${playTitle}">
            <i data-lucide="play"></i>
          </button>
          <button class="btn-msg-ctrl btn-pause-msg" type="button" title="${pauseTitle}" aria-label="${pauseTitle}" style="display:none;">
            <i data-lucide="pause"></i>
          </button>
          <button class="btn-msg-ctrl btn-resume-msg" type="button" title="${resumeTitle}" aria-label="${resumeTitle}" style="display:none;">
            <i data-lucide="play"></i>
          </button>
          <button class="btn-msg-ctrl btn-stop-msg" type="button" title="${stopTitle}" aria-label="${stopTitle}" disabled>
            <i data-lucide="square"></i>
          </button>
        </div>
      </div>
    `;

    // Translation info banner (if applicable)
    let translationBanner = '';
    if (wasTranslated) {
      translationBanner = `<div class="translation-info-banner"><i data-lucide="languages"></i> ${t('translating_response', 'Translated')}</div>`;
    } else if (translationFailed) {
      translationBanner = `<div class="translation-warning-banner"><i data-lucide="alert-triangle"></i> ${t('response_translation_failed', 'Could not translate this response. Showing the original.')}</div>`;
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

    // Action Highlight Banner — localized label
    let actionBanner = '';
    if (structuredCard && (structuredCard.recommended_action || structuredCard.next_best_action)) {
      const act = structuredCard.recommended_action || structuredCard.next_best_action;
      const nbaLabel = this.getLocalizedText({
        en: 'YOUR NEXT BEST ACTION:',
        hi: 'आपका अगला सबसे उपयुक्त कदम:',
        bn: 'আপনার পরবর্তী সেরা পদক্ষেপ:'
      });
      actionBanner = `
        <div class="next-best-action-banner">
          <i data-lucide="zap"></i>
          <strong>${nbaLabel}</strong> ${this.escapeHtml(act)}
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
        ${expertHeaderRowHtml}
        ${translationBanner}
        ${formattedParagraphs}
        ${cardHtml}
        ${actionBanner}
        ${followUpsHtml}
      </div>
    `;

    // Bind per-message speech control buttons
    const playBtn = msgDiv.querySelector('.btn-play-msg');
    const stopMsgBtn = msgDiv.querySelector('.btn-stop-msg');
    const pauseMsgBtn = msgDiv.querySelector('.btn-pause-msg');
    const resumeMsgBtn = msgDiv.querySelector('.btn-resume-msg');

    if (playBtn) {
      playBtn.addEventListener('click', () => {
        this.speakText(text, playBtn);
      });
    }
    if (stopMsgBtn) {
      stopMsgBtn.addEventListener('click', () => {
        this.stopSpeech();
      });
    }
    if (pauseMsgBtn) {
      pauseMsgBtn.addEventListener('click', () => {
        this.togglePauseResumeSpeech();
      });
    }
    if (resumeMsgBtn) {
      resumeMsgBtn.addEventListener('click', () => {
        this.togglePauseResumeSpeech();
      });
    }

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

    // Handle Auto-Read (TTS) if enabled by user and not suppressed
    if (this.autoReadEnabled && !suppressAutoRead && playBtn) {
      this.speakText(text, playBtn);
    }
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
