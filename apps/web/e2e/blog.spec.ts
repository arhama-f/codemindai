import { test, expect } from "@playwright/test";

test("visiting the blog lists posts and opens one with its content", async ({ page }) => {
  await page.goto("/blog");
  await expect(page.getByRole("heading", { name: "Blog" })).toBeVisible();

  const postLink = page.getByRole("heading", { name: "Why We Built CodeMind AI" });
  await expect(postLink).toBeVisible();
  await postLink.click();

  await page.waitForURL(/\/blog\/why-we-built-codemind-ai$/);
  await expect(page.getByRole("heading", { name: "Why We Built CodeMind AI" })).toBeVisible();
  await expect(page.getByText(/CodeMind AI exists to close that gap/)).toBeVisible();
});

test("the marketing homepage links to the blog", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("link", { name: "Blog" }).click();
  await page.waitForURL(/\/blog$/);
  await expect(page.getByRole("heading", { name: "Blog" })).toBeVisible();
});

test("sitemap.xml and robots.txt are served", async ({ request }) => {
  const sitemap = await request.get("/sitemap.xml");
  expect(sitemap.ok()).toBeTruthy();
  expect(await sitemap.text()).toContain("/blog");

  const robots = await request.get("/robots.txt");
  expect(robots.ok()).toBeTruthy();
});
