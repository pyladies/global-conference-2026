import { defineConfig } from "astro/config";
import { unified } from "@astrojs/markdown-remark";
import tailwindcss from "@tailwindcss/vite";
import sitemap from "@astrojs/sitemap";
import rehypeAutolinkHeadings from "rehype-autolink-headings";
import { autolinkConfig } from "./plugins/rehype-autolink-config";
import rehypeSlug from "rehype-slug";
import alpinejs from "@astrojs/alpinejs";
import icon from "astro-icon";
import { getSupportedLocales, defaultLang } from "./src/i18n/locales";

// https://astro.build/config
export default defineConfig({
	site: "https://2026.conference.pyladies.com",
	vite: {
		plugins: [tailwindcss()],
		define: {
			__DATE__: `'${new Date().toISOString()}'`,
		},
	},
	integrations: [
		sitemap({
			// Only the /<lang>/ pages carry content. The root and the locale-less
			// pages (/coc-reporting, /speaker/..., ...) are redirect stubs marked
			// noindex, so keep them out of the sitemap.
			filter: (page) => {
				const [, first] = new URL(page).pathname.split("/");
				return getSupportedLocales().includes(first);
			},
		}),
		alpinejs(),
		icon(),
	],
	markdown: {
		processor: unified({
			rehypePlugins: [
				rehypeSlug,
				// This adds links to headings
				[rehypeAutolinkHeadings, autolinkConfig],
			],
		}),
	},
	i18n: {
		locales: getSupportedLocales(),
		defaultLocale: defaultLang,
		routing: {
			prefixDefaultLocale: true,
			redirectToDefaultLocale: false,
		},
	}
});
