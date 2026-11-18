/**
 * PRANVYRA Centralized Internationalization (i18n) Engine
 * Seamless real-time translation across English, Hindi, and Bengali.
 */
(function() {
  window.PranvyraI18n = {
    currentLanguage: localStorage.getItem('pranvyra_lang') || 'en',
    dictionaries: {},
    isLoaded: false,

    async init() {
      await this.loadAllDictionaries();
      this.bindSwitcherEvents();
      this.applyTranslations(this.currentLanguage);
    },

    async loadAllDictionaries() {
      try {
        const [enRes, hiRes, bnRes] = await Promise.all([
          fetch('/static/js/i18n/en.json').then(r => r.json()),
          fetch('/static/js/i18n/hi.json').then(r => r.json()),
          fetch('/static/js/i18n/bn.json').then(r => r.json())
        ]);
        this.dictionaries = {
          en: enRes,
          hi: hiRes,
          bn: bnRes
        };
        this.isLoaded = true;
      } catch (err) {
        console.warn('Could not fetch i18n JSON files, falling back to embedded defaults:', err);
      }
    },

    bindSwitcherEvents() {
      document.querySelectorAll('.bhasha-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
          const lang = e.currentTarget.getAttribute('data-lang');
          if (lang && lang !== this.currentLanguage) {
            this.setLanguage(lang);
          }
        });
      });

      // Air-Twin language select dropdown
      const prefLangSelect = document.getElementById('prefLanguage');
      if (prefLangSelect) {
        prefLangSelect.addEventListener('change', (e) => {
          const lang = e.target.value;
          if (lang && lang !== this.currentLanguage) {
            this.setLanguage(lang);
          }
        });
      }
    },

    async setLanguage(lang) {
      if (!['en', 'hi', 'bn'].includes(lang)) lang = 'en';
      this.currentLanguage = lang;
      localStorage.setItem('pranvyra_lang', lang);
      document.documentElement.lang = lang;

      // Update switcher pills active class
      document.querySelectorAll('.bhasha-btn').forEach(btn => {
        btn.classList.toggle('active', btn.getAttribute('data-lang') === lang);
      });

      // Update Air-Twin dropdown value
      const prefLangSelect = document.getElementById('prefLanguage');
      if (prefLangSelect && prefLangSelect.value !== lang) {
        prefLangSelect.value = lang;
      }

      // Sync with global state
      if (window.PranvyraState) {
        window.PranvyraState.setLanguage(lang, false);
      }

      // Apply translations to entire DOM
      this.applyTranslations(lang);

      // Re-render Lucide icons for translated elements
      if (window.lucide) {
        window.lucide.createIcons();
      }

      // Inform user via localized toast
      const toasts = {
        en: 'Language set to English.',
        hi: 'भाषा बदलकर हिंदी कर दी गई है।',
        bn: 'ভাষা পরিবর্তন করে বাংলা করা হয়েছে।'
      };
      if (window.PranvyraAPI && window.PranvyraAPI.showToast) {
        window.PranvyraAPI.showToast(toasts[lang] || toasts.en, 'info');
      }

      // Sync with visitor profile on backend if API available
      if (window.PranvyraAPI && window.PranvyraAPI.updateUserProfile) {
        window.PranvyraAPI.updateUserProfile({ language_pref: lang }).catch(() => {});
      }

      // Emit event for other modules
      window.dispatchEvent(new CustomEvent('pranvyra:language_changed', { detail: { language: lang } }));
    },

    t(key, fallback = null) {
      const dict = this.dictionaries[this.currentLanguage] || this.dictionaries['en'] || {};
      if (dict && dict[key] !== undefined) {
        return dict[key];
      }
      // Fallback to English dict
      const enDict = this.dictionaries['en'] || {};
      if (enDict && enDict[key] !== undefined) {
        return enDict[key];
      }
      return fallback !== null ? fallback : key;
    },

    applyTranslations(lang) {
      const dict = this.dictionaries[lang] || this.dictionaries['en'] || {};
      if (!dict || Object.keys(dict).length === 0) return;

      // 1. Text content: [data-i18n]
      document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        const translation = dict[key];
        if (translation !== undefined) {
          // If element contains an icon or span, preserve the icon
          const icon = el.querySelector('i[data-lucide], svg');
          if (icon) {
            const iconClone = icon.cloneNode(true);
            el.innerHTML = '';
            el.appendChild(iconClone);
            el.appendChild(document.createTextNode(' ' + translation));
          } else {
            el.textContent = translation;
          }
        }
      });

      // 2. Placeholders: [data-i18n-placeholder]
      document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        const translation = dict[key];
        if (translation !== undefined) {
          el.setAttribute('placeholder', translation);
        }
      });

      // 3. Tooltips & Titles: [data-i18n-title]
      document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        const translation = dict[key];
        if (translation !== undefined) {
          el.setAttribute('title', translation);
        }
      });

      // 4. Accessibility: [data-i18n-aria]
      document.querySelectorAll('[data-i18n-aria]').forEach(el => {
        const key = el.getAttribute('data-i18n-aria');
        const translation = dict[key];
        if (translation !== undefined) {
          el.setAttribute('aria-label', translation);
        }
      });
    }
  };

  document.addEventListener('DOMContentLoaded', () => {
    window.PranvyraI18n.init();
  });
})();

