import type { Metadata } from "next";
import Link from "next/link";

import { getAllBlogPosts } from "@/lib/blog";

export const metadata: Metadata = {
  title: "Blog — CodeMind AI",
  description: "Notes on building an AI staff engineer that reads your actual code.",
};

export default function BlogIndexPage() {
  const posts = getAllBlogPosts();

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <h1 className="mb-8 text-2xl font-semibold">Blog</h1>
      <ul className="flex flex-col gap-6">
        {posts.map((post) => (
          <li key={post.slug}>
            <Link href={`/blog/${post.slug}`} className="block">
              <h2 className="text-lg font-medium hover:text-blue-400">{post.title}</h2>
              <p className="mt-1 text-sm text-gray-500">{post.date}</p>
              <p className="mt-2 text-gray-400">{post.description}</p>
            </Link>
          </li>
        ))}
      </ul>
    </main>
  );
}
