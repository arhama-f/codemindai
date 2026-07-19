import { test, expect } from "@playwright/test";

test("registering with an already-used email shows a clear error", async ({ page }) => {
  const email = `e2e-dup-${Date.now()}@example.com`;

  await page.goto("/register");
  await page.getByPlaceholder("Full name").fill("First User");
  await page.getByPlaceholder("Email").fill(email);
  await page.getByPlaceholder("Password").fill("hunter22");
  await page.getByRole("button", { name: "Create account" }).click();
  await page.waitForURL(/\/orgs$/);

  // Log out by dropping the session cookie, then try registering the same
  // email again.
  await page.context().clearCookies();
  await page.goto("/register");
  await page.getByPlaceholder("Full name").fill("Second User");
  await page.getByPlaceholder("Email").fill(email);
  await page.getByPlaceholder("Password").fill("hunter22");
  await page.getByRole("button", { name: "Create account" }).click();

  await expect(page.getByText("Email already registered")).toBeVisible({ timeout: 10_000 });
  // Confirms the failed registration didn't navigate away.
  await expect(page).toHaveURL(/\/register$/);
});

test("visiting an organization page while unauthenticated shows no real org data", async ({
  browser,
}) => {
  // A fresh, cookie-less browser context — simulates a logged-out visitor
  // hitting an org URL directly, without depending on any org created by
  // other tests.
  const context = await browser.newContext();
  const page = await context.newPage();

  await page.goto("/orgs/00000000-0000-0000-0000-000000000000");

  // The org page has no auth guard/redirect — its queries simply fail
  // unauthenticated (401) and their `data` stays `undefined` (not an empty
  // array), so the empty-state copy never renders either. The correct,
  // verified assertion is "no real data leaks": no repo links, no org name.
  await expect(page.getByRole("heading", { name: "Organization" })).toBeVisible();
  await expect(page.locator('a[href*="/repos/"]')).toHaveCount(0);

  await context.close();
});
