/**
 * APS System Theme Manager
 * Handles theme persistence and application across all pages.
 */

const THEME_KEY = 'aps_system_theme';

/**
 * Apply the theme to the document
 * @param {string} theme - 'light', 'gray', or 'dark'
 */
function applyTheme(theme) {
    if (!theme) theme = localStorage.getItem(THEME_KEY) || 'light';
    
    // Set data-theme on both html and body for maximum compatibility
    document.documentElement.setAttribute('data-theme', theme);
    document.body.setAttribute('data-theme', theme);
    
    // Save to localStorage
    localStorage.setItem(THEME_KEY, theme);
    
    // Dispatch event for components that might need to react
    window.dispatchEvent(new CustomEvent('themeChanged', { detail: { theme } }));
    
    // Update any theme switcher buttons on the page
    updateThemeUI(theme);
}

/**
 * Update UI elements related to theme selection
 * @param {string} theme 
 */
function updateThemeUI(theme) {
    // Update button active states if they exist
    const buttons = {
        'light': ['themeLightBtn', 'btnThemeLight'],
        'gray': ['themeGrayBtn', 'btnThemeGray'],
        'dark': ['themeDarkBtn', 'btnThemeDark']
    };
    
    // Remove active class from all possible theme buttons
    Object.values(buttons).flat().forEach(id => {
        const el = document.getElementById(id);
        if (el) el.classList.remove('active');
    });
    
    // Add active class to current theme buttons
    if (buttons[theme]) {
        buttons[theme].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.classList.add('active');
        });
    }
}

// Initialize theme on load
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem(THEME_KEY) || 'light';
    applyTheme(savedTheme);
});

// Polyfill for pages that might have their own setTheme
if (typeof window.setTheme !== 'function') {
    window.setTheme = applyTheme;
}
