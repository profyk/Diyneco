// Kept free of React so root layouts (server components) can import it.

export const THEME_KEY = "diyneco.theme";

/** Inline script for <head>: sets data-theme from the saved choice before the first paint. */
export const THEME_SCRIPT = `(function(){try{var t=localStorage.getItem("${THEME_KEY}");if(t==="light"||t==="dark"){document.documentElement.dataset.theme=t}}catch(e){}})();`;
