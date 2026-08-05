import fs from "node:fs";
import path from "node:path";

import type { Metadata } from "next";
import { notFound } from "next/navigation";

import { getAllBlogPosts, getBlogPostMeta } from "@/lib/blog";

export function generateStaticParams() {
  return getAllBlogPosts().map((post) => ({ slug: post.slug }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ slug: string }>;
}): Promise<Metadata> {
  const { slug } = await params;
  const post = getBlogPostMeta(slug);
  if (!post) return {};
  return { title: `${post.title} — CodeMind AI`, description: post.description };
}

export default async function BlogPostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = getBlogPostMeta(slug);
  if (!post) notFound();

  const contentDir = path.join(process.cwd(), "content", "blog");
  if (!fs.existsSync(path.join(contentDir, `${slug}.mdx`))) notFound();

  const { default: Content } = await import(`@/content/blog/${slug}.mdx`);

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <h1 className="mb-1 text-2xl font-semibold">{post.title}</h1>
      <p className="mb-8 text-sm text-gray-500">{post.date}</p>
      <article className="prose prose-invert max-w-none">
        <Content />
      </article>
    </main>
  );
}
