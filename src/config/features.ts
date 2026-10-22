/**
 * Feature switches for things that are built but not offered right now.
 * Flip a switch back on to bring the feature back; nothing is deleted.
 */

/** The interface ships EN/DE/ZH-CN chrome strings; deeper labels fall back to English. */
export const APP_LANGUAGE_SWITCHING_ENABLED = true;

/** Keep paperwork language project-scoped and hidden until its PDF support is complete. */
export const DOCUMENT_LANGUAGE_SWITCHING_ENABLED = false;
