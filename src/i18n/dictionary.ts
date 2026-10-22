/**
 * Minimal EN/DE/ZH-CN chrome translation (no dependency).
 *
 * The app's domain vocabulary (shot sizes, departments, paperwork labels) is
 * hundreds of strings and stays English for now — translating the *chrome*
 * (save states, dashboard, nav) covers the daily driver for German crews
 * without a risky string-by-string migration. Every key exists in both
 * languages; `t()` falls back to English when a language or key is missing.
 */
export type AppLanguage = 'en' | 'de' | 'zh-CN';

const LANG_KEY = 'openshotdesigner_lang';

export const SUPPORTED_LANGUAGES: AppLanguage[] = ['en', 'de', 'zh-CN'];

export const LANGUAGE_LABELS: Record<AppLanguage, string> = {
  en: 'English',
  de: 'Deutsch',
  'zh-CN': '简体中文',
};

export const detectLanguage = (): AppLanguage => {
  try {
    const stored = localStorage.getItem(LANG_KEY);
    if (stored === 'de' || stored === 'en' || stored === 'zh-CN') return stored;
    const browserLanguage = navigator.language.toLowerCase();
    if (browserLanguage.startsWith('zh')) return 'zh-CN';
    return browserLanguage.startsWith('de') ? 'de' : 'en';
  } catch {
    return 'en';
  }
};

export const persistLanguage = (lang: AppLanguage): void => {
  try {
    localStorage.setItem(LANG_KEY, lang);
  } catch {
    // Preference only — never break the app over it.
  }
};

const en = {
  'save.saving': 'Saving…',
  'save.saved': 'Saved locally',
  'save.error': 'Save failed',
  'save.retry': 'Retry',
  'nav.dashboard': 'All projects (dashboard)',
  'nav.rename': 'Click to rename project',
  'nav.language': 'Language',
  'dashboard.title': 'Projects',
  'dashboard.new': 'New project',
  'dashboard.open': 'Open',
  'dashboard.backupAvailable': 'Safety copy available',
  'dashboard.restoreBackup': 'Restore safety copy',
  'conflict.reload': 'Reload',
  'common.close': 'Close',
  'common.cancel': 'Cancel',
  'common.delete': 'Delete',
  'common.save': 'Save',
} as const;

export type I18nKey = keyof typeof en;

const de: Record<I18nKey, string> = {
  'save.saving': 'Speichert…',
  'save.saved': 'Lokal gespeichert',
  'save.error': 'Speichern fehlgeschlagen',
  'save.retry': 'Erneut versuchen',
  'nav.dashboard': 'Alle Projekte (Übersicht)',
  'nav.rename': 'Klicken zum Umbenennen',
  'nav.language': 'Sprache',
  'dashboard.title': 'Projekte',
  'dashboard.new': 'Neues Projekt',
  'dashboard.open': 'Öffnen',
  'dashboard.backupAvailable': 'Sicherheitskopie vorhanden',
  'dashboard.restoreBackup': 'Sicherheitskopie wiederherstellen',
  'conflict.reload': 'Neu laden',
  'common.close': 'Schließen',
  'common.cancel': 'Abbrechen',
  'common.delete': 'Löschen',
  'common.save': 'Speichern',
};

const zhCN: Record<I18nKey, string> = {
  'save.saving': '正在保存…',
  'save.saved': '已保存到此浏览器',
  'save.error': '保存失败',
  'save.retry': '重试',
  'nav.dashboard': '所有项目（项目总览）',
  'nav.rename': '点击重命名项目',
  'nav.language': '界面语言',
  'dashboard.title': '项目',
  'dashboard.new': '新建项目',
  'dashboard.open': '打开',
  'dashboard.backupAvailable': '有安全副本可用',
  'dashboard.restoreBackup': '恢复安全副本',
  'conflict.reload': '重新加载',
  'common.close': '关闭',
  'common.cancel': '取消',
  'common.delete': '删除',
  'common.save': '保存',
};

const dictionaries: Record<AppLanguage, Record<I18nKey, string>> = { en, de, 'zh-CN': zhCN };

export const translate = (lang: AppLanguage, key: I18nKey): string =>
  dictionaries[lang]?.[key] ?? en[key];
