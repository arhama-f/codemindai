import createMDX from "@next/mdx";
import type { NextConfig } from "next";
import remarkFrontmatter from "remark-frontmatter";
import remarkMdxFrontmatter from "remark-mdx-frontmatter";
import { withSentryConfig } from "@sentry/nextjs";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Only affects `next build`'s output shape (used by apps/web/Dockerfile);
  // has no effect on `next dev`.
  output: "standalone",
  pageExtensions: ["ts", "tsx", "mdx"],
};

const withMDX = createMDX({
  // Without these, the `---` frontmatter block in content/blog/*.mdx is
  // treated as literal Markdown and rendered as visible text — these strip
  // it from the compiled output. Frontmatter itself is read separately via
  // gray-matter in lib/blog.ts for list/metadata display.
  options: {
    remarkPlugins: [remarkFrontmatter, remarkMdxFrontmatter],
  },
});

// Wraps outermost so MDX's plugin wiring above runs first; source-map
// upload silently no-ops without SENTRY_AUTH_TOKEN/org/project set — never
// fails the build, matches this repo's "inert unless configured" convention.
export default withSentryConfig(withMDX(nextConfig), {
  org: process.env.SENTRY_ORG,
  project: process.env.SENTRY_PROJECT,
  silent: true,
  disableLogger: true,
  // No SENTRY_AUTH_TOKEN configured (see docs/architecture.md's "inert
  // unless configured" convention) — there's nowhere to upload source maps,
  // so skip generating them rather than build them and discard.
  sourcemaps: { disable: true },
});
