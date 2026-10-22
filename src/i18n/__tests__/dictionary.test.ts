import { describe, expect, it } from 'vitest';
import { LANGUAGE_LABELS, SUPPORTED_LANGUAGES, translate, type I18nKey } from '../dictionary';

const KEYS: I18nKey[] = [
  'save.saving',
  'save.saved',
  'save.error',
  'save.retry',
  'nav.dashboard',
  'nav.rename',
  'nav.language',
  'dashboard.title',
  'dashboard.new',
  'dashboard.open',
  'dashboard.backupAvailable',
  'dashboard.restoreBackup',
  'conflict.reload',
  'common.close',
  'common.cancel',
  'common.delete',
  'common.save',
];

describe('i18n dictionary', () => {
  it('covers every key in every supported language with no empty strings', () => {
    for (const lang of SUPPORTED_LANGUAGES) {
      for (const key of KEYS) {
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
});
