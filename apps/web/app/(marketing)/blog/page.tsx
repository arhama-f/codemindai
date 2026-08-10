import type { Metadata } from "next";
import Link from "next/link";

import { Card } from "@/components/ui/card";
import { getAllBlogPosts } from "@/lib/blog";

export const metadata: Metadata = {
  title: "Blog — CodeMind AI",
  description: "Notes on building an AI staff engineer that reads your actual code.",
  openGraph: {
    title: "Blog — CodeMind AI",
    description: "Notes on building an AI staff engineer that reads your actual code.",
  },
};

export default function BlogIndexPage() {
  const posts = getAllBlogPosts();

  return (
    <main className="mx-auto max-w-3xl px-6 py-24 md:py-32">
      <div className="mb-16 text-center">
        <h1 className="text-4xl font-semibold tracking-tight md:text-5xl">Blog</h1>
        <p className="mt-4 text-lg text-muted-foreground">
          Notes on building an AI staff engineer that reads your actual code.
        </p>
      </div>
      <div className="flex flex-col gap-4">
        {posts.map((post) => (
          <Link key={post.slug} href={`/blog/${post.slug}`}>
            <Card className="border-border/60 p-6 shadow-sm transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg md:p-8">
              <p className="mb-2 text-sm text-muted-foreground">{post.date}</p>
              <h2 className="mb-2 text-xl font-semibold">{post.title}</h2>
              <p className="text-muted-foreground">{post.description}</p>
            </Card>
          </Link>
        ))}
      </div>
    </main>
  );
}
