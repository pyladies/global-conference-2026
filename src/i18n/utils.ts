import { defaultLang, getSupportedLocales, isValidLocale } from './locales';
import translationsData from './translations.json';

const translations = translationsData as Record<string, Record<string, string>>;

export function getLangFromUrl(url: URL): string {
  const [, lang] = url.pathname.split('/');
  if (lang && isValidLocale(lang)) return lang;
  return defaultLang;
}

export function useTranslations(lang: string) {
  return function t(key: string): string {
    // For default language, return the source string directly
    if (lang === defaultLang) {
      return key;
    }
    
    // For other languages, look up in translations JSON, fallback to source string
    const langTranslations = translations[lang] || {};
    return langTranslations[key] || key;
  }
}

export function useTranslatedPath(lang: string) {
  return function translatePath(path: string, l: string = lang) {
    return `/${l}${path}`
  }
}

export const localizePath = (
  path: string = "/",
  locale: string | null = null,
): string => {
  if (!locale) {
    locale = defaultLang;
  }

  const locales = getSupportedLocales();
  let pathSegments = path.split("/").filter((segment) => segment !== "");

  // Remove locale from pathSegments if present
  if (pathSegments.length > 0 && locales.includes(pathSegments[0])) {
    pathSegments.shift();
  }

  // Prepend locale
  pathSegments = [locale, ...pathSegments];

  return "/" + pathSegments.join("/");
};

/**
 * Rewrite root-relative links in a compiled HTML string so they point at the
 * given locale: `href="/coc-reporting"` becomes `href="/fr/coc-reporting"`.
 * A link that already carries a locale prefix is re-pointed to the given one,
 * since the same compiled Markdown is shared by every language page.
 *
 * External and protocol-relative URLs are untouched, and so are links to
 * static assets such as `/files/report.pdf`, which live outside the locale
 * folders. An asset is recognised by a file extension on its last segment.
 */
export const localizeLinks = (html: string, lang: string): string =>
  html.replace(/href="\/(?!\/)([^"]*)"/g, (match, path: string) => {
    const lastSegment = path.split(/[?#]/)[0].split("/").pop() ?? "";
    if (lastSegment.includes(".")) return match;
    return `href="${localizePath(`/${path}`, lang)}"`;
  });
