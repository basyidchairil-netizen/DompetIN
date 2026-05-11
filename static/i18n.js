/**
 * Internationalization (i18n) Manager for Dompetin
 * Handles Language switching between English and Indonesian
 * with localStorage persistence
 */

(function() {
    'use strict';

    // Language storage key
    const LANGUAGE_KEY = 'dompetin-language';
    
    // Available languages
    const LANGUAGES = {
        EN: 'en',
        ID: 'id'
    };

    // Current language
    let currentLanguage = localStorage.getItem(LANGUAGE_KEY) || LANGUAGES.ID;
    
    // Translations cache
    let translations = null;

    /**
     * Load translations from JSON file
     */
    async function loadTranslations() {
        try {
            const response = await fetch('./static/translations.json');
            translations = await response.json();
            return true;
        } catch (error) {
            console.error('Error loading translations:', error);
            return false;
        }
    }

    /**
     * Get translation for a key
     */
    function t(key) {
        if (!translations) {
            console.warn('Translations not loaded yet');
            return key;
        }
        
        const langTranslations = translations[currentLanguage];
        if (!langTranslations) {
            console.warn('Language not found:', currentLanguage);
            return key;
        }
        
        return langTranslations[key] || key;
    }

    /**
     * Get current language
     */
    function getCurrentLanguage() {
        return currentLanguage;
    }

    /**
     * Get all available languages
     */
    function getAvailableLanguages() {
        return LANGUAGES;
    }

    /**
     * Set language and update UI
     */
    async function setLanguage(lang) {
        if (!Object.values(LANGUAGES).includes(lang)) {
            console.error('Invalid language:', lang);
            return;
        }

        currentLanguage = lang;
        
        // Save to localStorage
        localStorage.setItem(LANGUAGE_KEY, lang);
        
        // Update HTML lang attribute
        document.documentElement.lang = lang;
        
        // Update all translatable elements
        updatePageTranslations();
        
        // Update language switcher buttons
        updateLanguageButtons();
        
        // Dispatch event for custom handling
        document.dispatchEvent(new CustomEvent('languageChanged', { detail: { language: lang } }));
    }

    /**
     * Toggle between languages
     */
    function toggleLanguage() {
        const newLang = currentLanguage === LANGUAGES.ID ? LANGUAGES.EN : LANGUAGES.ID;
        setLanguage(newLang);
    }

    /**
     * Update all translatable elements on the page
     */
    function updatePageTranslations() {
        // Update elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(function(element) {
            const key = element.getAttribute('data-i18n');
            const translation = t(key);
            
            // Handle different element types
            if (element.tagName === 'INPUT' && element.getAttribute('placeholder')) {
                element.placeholder = translation;
            } else if (element.tagName === 'INPUT' && element.getAttribute('type') !== 'submit') {
                // Skip input values for non-submit inputs
            } else {
                element.textContent = translation;
            }
        });

        // Update elements with data-i18n-placeholder attribute
        document.querySelectorAll('[data-i18n-placeholder]').forEach(function(element) {
            const key = element.getAttribute('data-i18n-placeholder');
            element.placeholder = t(key);
        });

        // Update elements with data-i18n-title attribute
        document.querySelectorAll('[data-i18n-title]').forEach(function(element) {
            const key = element.getAttribute('data-i18n-title');
            element.title = t(key);
        });

        // Update document title if data-i18n-title attribute exists on title element
        const titleElement = document.querySelector('title[data-i18n]');
        if (titleElement) {
            const key = titleElement.getAttribute('data-i18n');
            document.title = t(key);
        }
    }

    /**
     * Update language switcher buttons to reflect current state
     */
    function updateLanguageButtons() {
        // Update all language toggle buttons
        const buttons = document.querySelectorAll('.language-toggle');
        
        buttons.forEach(function(button) {
            // Update button text or icon
            const langText = button.querySelector('.lang-text');
            if (langText) {
                langText.textContent = currentLanguage === LANGUAGES.ID ? 'ID' : 'EN';
            }
            
            // Update button title
            const nextLang = currentLanguage === LANGUAGES.ID ? 'English' : 'Indonesia';
            button.setAttribute('title', 'Switch to ' + nextLang);
        });

        // Update dropdown if exists
        const dropdown = document.getElementById('language-dropdown');
        if (dropdown) {
            dropdown.value = currentLanguage;
        }

        // Update any language indicator text
        const langIndicators = document.querySelectorAll('.language-indicator');
        langIndicators.forEach(function(indicator) {
            indicator.textContent = currentLanguage === LANGUAGES.ID ? 'Indonesia' : 'English';
        });
    }

    /**
     * Create language toggle button HTML
     */
    function createLanguageToggleButton() {
        return `
            <button class="language-toggle p-2 rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors duration-200" 
                    onclick="window.i18nManager.toggleLanguage()" 
                    aria-label="Toggle language">
                <span class="lang-text font-medium text-sm">${currentLanguage === LANGUAGES.ID ? 'ID' : 'EN'}</span>
                <i class="fas fa-globe ml-1"></i>
            </button>
        `;
    }

    /**
     * Create language dropdown HTML
     */
    function createLanguageDropdown() {
        return `
            <select id="language-dropdown" 
                    class="language-dropdown px-3 py-1.5 rounded-lg border bg-white dark:bg-gray-700 dark:border-gray-600 text-gray-700 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    onchange="window.i18nManager.setLanguage(this.value)">
                <option value="id" ${currentLanguage === LANGUAGES.ID ? 'selected' : ''}>
                    🇮🇩 Indonesia
                </option>
                <option value="en" ${currentLanguage === LANGUAGES.EN ? 'selected' : ''}>
                    🇬🇧 English
                </option>
            </select>
        `;
    }

    /**
     * Create language toggle for sidebar
     */
    function createSidebarLanguageToggle() {
        return `
            <div class="language-switcher px-4 py-2 mt-4 border-t border-emerald-600">
                <div class="flex items-center justify-between">
                    <span class="text-sm text-emerald-200">
                        <i class="fas fa-globe mr-2"></i>
                        <span class="language-indicator">${currentLanguage === LANGUAGES.ID ? 'Indonesia' : 'English'}</span>
                    </span>
                    <button onclick="window.i18nManager.toggleLanguage()" 
                            class="text-emerald-200 hover:text-white text-sm font-medium">
                        ${currentLanguage === LANGUAGES.ID ? 'EN' : 'ID'}
                    </button>
                </div>
            </div>
        `;
    }

    /**
     * Initialize the i18n manager
     */
    async function init() {
        // Load translations
        const loaded = await loadTranslations();
        if (!loaded) {
            console.error('Failed to load translations');
            return;
        }

        // Apply saved language
        document.documentElement.lang = currentLanguage;
        
        // Update page translations
        updatePageTranslations();
        
        // Update buttons
        updateLanguageButtons();
        
        console.log('i18n initialized with language:', currentLanguage);
    }

    // Expose API globally
    window.i18nManager = {
        languages: LANGUAGES,
        currentLanguage: currentLanguage,
        setLanguage: setLanguage,
        toggleLanguage: toggleLanguage,
        t: t,
        getCurrentLanguage: getCurrentLanguage,
        getAvailableLanguages: getAvailableLanguages,
        updatePageTranslations: updatePageTranslations,
        createLanguageToggleButton: createLanguageToggleButton,
        createLanguageDropdown: createLanguageDropdown,
        createSidebarLanguageToggle: createSidebarLanguageToggle
    };

    // Initialize when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        init();
    });

    // Also initialize immediately in case DOM is already loaded
    if (document.readyState !== 'loading') {
        init();
    }

})();

