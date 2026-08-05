import { test, expect } from "@playwright/test";

test.setTimeout(120_000);

const API_URL = "http://localhost:8010";

function extractToken(htmlBody: string, pathSegment: string): string {
  return htmlBody.split(`${pathSegment}/`)[1].split('"')[0];
}

test("register, verify email via emailed link", async ({ page, request }) => {
  const unique = Date.now();
  const email = `e2e-verify-${unique}@example.com`;

  await test.step("register", async () => {
    await page.goto("/register");
    await page.getByPlaceholder("Full name").fill("Verify Tester");
    await page.getByPlaceholder("Email").fill(email);
    await page.getByPlaceholder("Password").fill("hunter22");
    await page.getByRole("button", { name: "Create account" }).click();
    await page.waitForURL(/\/orgs$/);
    await expect(page.getByText("Please verify your email address.")).toBeVisible();
  });

  await test.step("follow the emailed verification link", async () => {
    const response = await request.get(`${API_URL}/api/testing/last-email?to=${email}`);
    expect(response.ok()).toBeTruthy();
    const { html_body: htmlBody } = await response.json();
    const token = extractToken(htmlBody, "/verify-email");

    await page.goto(`/verify-email/${token}`);
    await expect(page.getByText("Email verified")).toBeVisible({ timeout: 15_000 });
  });

  await test.step("banner is gone after verifying", async () => {
    await page.goto("/orgs");
    await expect(page.getByText("Please verify your email address.")).not.toBeVisible();
  });
});

test("forgot password, reset via emailed link, log in with new password", async ({
  page,
  request,
}) => {
  const unique = Date.now();
  const email = `e2e-reset-${unique}@example.com`;

  await test.step("register", async () => {
    await page.goto("/register");
    await page.getByPlaceholder("Full name").fill("Reset Tester");
    await page.getByPlaceholder("Email").fill(email);
    await page.getByPlaceholder("Password").fill("old-password");
    await page.getByRole("button", { name: "Create account" }).click();
    await page.waitForURL(/\/orgs$/);
  });

  await test.step("request a password reset", async () => {
    await page.goto("/login");
    await page.getByText("Forgot your password?").click();
    await page.waitForURL(/\/forgot-password$/);
    await page.getByPlaceholder("Email").fill(email);
    await page.getByRole("button", { name: "Send reset link" }).click();
    await expect(page.getByText("Check your email")).toBeVisible();
  });

  await test.step("reset the password via the emailed link", async () => {
    const response = await request.get(`${API_URL}/api/testing/last-email?to=${email}`);
    expect(response.ok()).toBeTruthy();
    const { html_body: htmlBody } = await response.json();
    const token = extractToken(htmlBody, "/reset-password");

    await page.goto(`/reset-password/${token}`);
    await page.getByPlaceholder("New password").fill("new-password");
    await page.getByRole("button", { name: "Reset password" }).click();
    await page.waitForURL(/\/login$/);
  });

  await test.step("log in with the new password", async () => {
    await page.getByPlaceholder("Email").fill(email);
    await page.getByPlaceholder("Password").fill("new-password");
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.waitForURL(/\/orgs$/);
  });
});
