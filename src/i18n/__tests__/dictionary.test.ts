import { afterEach, describe, expect, it } from 'vitest';
import {
  detectLanguage,
  I18N_KEYS,
  LANGUAGE_LABELS,
  SUPPORTED_LANGUAGES,
  translate,
} from '../dictionary';

afterEach(() => localStorage.clear());

describe('i18n dictionary', () => {
  it('covers every key in every supported language with no empty strings', () => {
    for (const lang of SUPPORTED_LANGUAGES) {
      for (const key of I18N_KEYS) {
        const value = translate(lang, key);
        expect(value, `${lang}:${key}`).toBeTruthy();
      }
    }
  });

  it('falls back to English for unknown languages', () => {
    expect(translate('fr' as never, 'save.saved')).toBe(translate('en', 'save.saved'));
  });

  it('offers a native Simplified Chinese label and translations', () => {
    expect(LANGUAGE_LABELS['zh-CN']).toBe('简体中文');
    expect(translate('zh-CN', 'dashboard.title')).toBe('项目');
    expect(translate('zh-CN', 'common.cancel')).toBe('取消');
  });

  it('restores a saved Simplified Chinese preference', () => {
    localStorage.setItem('openshotdesigner_lang', 'zh-CN');
    expect(detectLanguage()).toBe('zh-CN');
  });
});
