import { test, expect } from "@playwright/test";

test("Analyze flow: paste diff and render roadmap", async ({
  page,
  baseURL,
}) => {
  await page.goto(baseURL || "http://localhost:5173");

  // Ensure page loaded
  await expect(
    page.locator("h2", { hasText: "Analyze Git Diff" }),
  ).toBeVisible();

  const diff = `diff --git a/README.md b/README.md\nindex 000..111\n+Added line\n-Removed line`;

  // Fill textarea and click Analyze
  await page.fill("textarea", diff);
  await page.click('button:has-text("Analyze")');

  // Wait for roadmap to appear
  await expect(page.locator("h3", { hasText: "Review Roadmap" })).toBeVisible();

  // Expect at least one roadmap item to show up
  const items = page.locator("ul li");
  await expect(items.first()).toBeVisible();

  // Check Cognitive Load / Thermometer appears in Review Roadmap
  await expect(
    page.locator(".review-map strong", { hasText: "Cognitive Load" }),
  ).toBeVisible();
});
