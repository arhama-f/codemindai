import createMDX from "@next/mdx";
import type { NextConfig } from "next";
import remarkFrontmatter from "remark-frontmatter";
import remarkMdxFrontmatter from "remark-mdx-frontmatter";

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

export default withMDX(nextConfig);
