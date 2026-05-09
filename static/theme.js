/**
 * Theme Manager for Dompetin
 * Handles Light, Dark, and Auto theme modes with system preference detection
 * and localStorage persistence
 */

(function() {
    'use strict';

    // Theme storage key
    const THEME_KEY = 'dompetin-theme';
    
    // Available themes
    const THEMES = {
        LIGHT: 'light',
        DARK: 'dark',
        AUTO: 'auto'
    };

    // Current theme
    let currentTheme = localStorage.getItem(THEME_KEY) || THEMES.AUTO;

    /**
     * Get system preferred color scheme
     */
    function getSystemPreference() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return THEMES.DARK;
        }
        return THEMES.LIGHT;
    }

    /**
     * Get the actual theme to apply based on current mode
     */
    function getEffectiveTheme() {
        if (currentTheme === THEMES.AUTO) {
            return getSystemPreference();
        }
        return currentTheme;
    }

    /**
     * Apply theme to the document
     */
    function applyTheme() {
        const effectiveTheme = getEffectiveTheme();
        
        // Apply to document
        document.documentElement.setAttribute('data-theme', effectiveTheme);
        
        // Add/remove dark class for Tailwind CSS
        if (effectiveTheme === THEMES.DARK) {
            document.documentElement.classList.add('dark');
        } else {
            document.documentElement.classList.remove('dark');
        }

        // Update all theme toggle buttons
        updateThemeButtons();
        
        // Save to localStorage
        localStorage.setItem(THEME_KEY, currentTheme);
    }

    /**
     * Update all theme toggle buttons to reflect current state
     */
    function updateThemeButtons() {
        const buttons = document.querySelectorAll('.theme-toggle');
        
        buttons.forEach(button => {
            const icons = button.querySelectorAll('.theme-icon');
            icons.forEach(icon => {
                icon.style.display = 'none';
            });
            
            // Show appropriate icon
            const activeIcon = button.querySelector(`.theme-icon-${currentTheme}`);
            if (activeIcon) {
                activeIcon.style.display = 'inline-block';
            }
            
            // Update button title/aria-label
            const nextTheme = getNextTheme();
            button.setAttribute('title', `Theme: ${currentTheme} (Click to change to ${nextTheme})`);
            button.setAttribute('aria-label', `Current theme: ${currentTheme}. Click to switch to ${nextTheme}`);
        });

        // Update dropdown if exists
        const dropdown = document.getElementById('theme-dropdown');
        if (dropdown) {
            dropdown.value = currentTheme;
        }
    }

    /**
     * Get the next theme in cycle
     */
    function getNextTheme() {
        switch(currentTheme) {
            case THEMES.LIGHT:
                return THEMES.DARK;
            case THEMES.DARK:
                return THEMES.AUTO;
            case THEMES.AUTO:
                return THEMES.LIGHT;
            default:
                return THEMES.AUTO;
        }
    }

    /**
     * Cycle to next theme
     */
    function cycleTheme() {
        switch(currentTheme) {
            case THEMES.LIGHT:
                currentTheme = THEMES.DARK;
                break;
            case THEMES.DARK:
                currentTheme = THEMES.AUTO;
                break;
            case THEMES.AUTO:
            default:
                currentTheme = THEMES.LIGHT;
                break;
        }
        applyTheme();
    }

    /**
     * Set specific theme
     */
    function setTheme(theme) {
        if (Object.values(THEMES).includes(theme)) {
            currentTheme = theme;
            applyTheme();
        }
    }

    /**
     * Listen for system theme changes
     */
    function initSystemThemeListener() {
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            mediaQuery.addEventListener('change', (e) => {
                if (currentTheme === THEMES.AUTO) {
                    applyTheme();
                }
            });
        }
    }

    /**
     * Create theme toggle button HTML
     */
    function createThemeToggleButton() {
        return `
            <button class="theme-toggle p-2 rounded-lg bg-gray-200 dark:bg-gray-700 hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors duration-200" 
                    onclick="window.themeManager.cycleTheme()" 
                    aria-label="Toggle theme">
                <span class="theme-icon theme-icon-light text-yellow-500">
                    <i class="fas fa-sun"></i>
                </span>
                <span class="theme-icon theme-icon-dark text-gray-300">
                    <i class="fas fa-moon"></i>
                </span>
                <span class="theme-icon theme-icon-auto text-gray-500 dark:text-gray-400">
                    <i class="fas fa-circle-half-stroke"></i>
                </span>
            </button>
        `;
    }

    /**
     * Create theme dropdown HTML (alternative to toggle)
     */
    function createThemeDropdown() {
        return `
            <select id="theme-dropdown" 
                    class="theme-dropdown px-3 py-1.5 rounded-lg border bg-white dark:bg-gray-700 dark:border-gray-600 text-gray-700 dark:text-gray-200 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    onchange="window.themeManager.setTheme(this.value)">
                <option value="light" ${currentTheme === THEMES.LIGHT ? 'selected' : ''}>
                    ☀️ Light
                </option>
                <option value="dark" ${currentTheme === THEMES.DARK ? 'selected' : ''}>
                    🌙 Dark
                </option>
                <option value="auto" ${currentTheme === THEMES.AUTO ? 'selected' : ''}>
                    🔄 Auto (System)
                </option>
            </select>
        `;
    }

    // Expose API globally
    window.themeManager = {
        themes: THEMES,
        currentTheme: currentTheme,
        cycleTheme: cycleTheme,
        setTheme: setTheme,
        getEffectiveTheme: getEffectiveTheme,
        createThemeToggleButton: createThemeToggleButton,
        createThemeDropdown: createThemeDropdown
    };

    // Initialize on DOM ready
    document.addEventListener('DOMContentLoaded', function() {
        initSystemThemeListener();
        applyTheme();
    });

    // Also apply immediately in case DOM is already loaded
    if (document.readyState !== 'loading') {
        initSystemThemeListener();
        applyTheme();
    }

})();

