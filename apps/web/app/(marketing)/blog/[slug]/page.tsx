import fs from "node:fs";
import path from "node:path";

import type { Metadata } from "next";
import { ArrowLeft } from "lucide-react";
import Link from "next/link";
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
  const title = `${post.title} — CodeMind AI`;
  return {
    title,
    description: post.description,
    openGraph: { title, description: post.description },
  };
}

export default async function BlogPostPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const post = getBlogPostMeta(slug);
  if (!post) notFound();

  const contentDir = path.join(process.cwd(), "content", "blog");
  if (!fs.existsSync(path.join(contentDir, `${slug}.mdx`))) notFound();

  const { default: Content } = await import(`@/content/blog/${slug}.mdx`);

  return (
    <main className="mx-auto max-w-2xl px-6 py-24 md:py-32">
      <Link
        href="/blog"
        className="mb-8 inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-foreground"
      >
        <ArrowLeft className="size-3.5" />
        Back to blog
      </Link>
      <h1 className="mb-2 text-3xl font-semibold tracking-tight md:text-4xl">{post.title}</h1>
      <p className="mb-10 text-sm text-muted-foreground">{post.date}</p>
      <article className="prose prose-invert prose-lg max-w-none prose-headings:tracking-tight prose-a:text-primary">
        <Content />
      </article>
    </main>
  );
}
