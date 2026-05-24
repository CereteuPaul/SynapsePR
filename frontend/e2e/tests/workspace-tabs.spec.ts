import { test, expect } from "@playwright/test";

test("Workspace tabs switch panels and repository context", async ({
  page,
  baseURL,
}) => {
  await page.goto(baseURL || "http://localhost:5173");

  await expect(page.getByText("Multi-tenant review workspace")).toBeVisible();

  await expect(
    page.locator(".nav-panel").getByRole("button", { name: "Dashboard" }),
  ).toBeVisible();
  await expect(
    page.locator(".nav-panel").getByRole("button", { name: "Repositories" }),
  ).toBeVisible();
  await expect(
    page
      .locator(".nav-panel")
      .getByRole("button", { name: "Active PR Reviews" }),
  ).toBeVisible();
  await expect(
    page.locator(".nav-panel").getByRole("button", { name: "Team Settings" }),
  ).toBeVisible();

  await expect(
    page.locator(".canvas-tabs-card").getByRole("button", { name: "Overview" }),
  ).toBeVisible();

  await page
    .locator(".nav-panel")
    .getByRole("button", { name: "Repositories" })
    .click();
  await expect(page.getByText("Selected repository:")).toBeVisible();

  await page
    .locator(".nav-panel")
    .getByRole("button", { name: "Active PR Reviews" })
    .click();
  await expect(page.getByText("Harden diff ingestion")).toBeVisible();

  await page
    .locator(".nav-panel")
    .getByRole("button", { name: "Team Settings" })
    .click();
  await expect(page.getByText("Auto-assign reviewers")).toBeVisible();

  await page
    .locator(".canvas-tabs-card")
    .getByRole("button", { name: "Security / Risk" })
    .click();
  await expect(page.getByText("Trust boundaries and drift")).toBeVisible();

  await page
    .locator(".canvas-tabs-card")
    .getByRole("button", { name: "Interactive AI Coach" })
    .click();
  await expect(page.getByText("Review assistant")).toBeVisible();
  await expect(page.getByText("Suggested prompts")).toBeVisible();

  await page.locator(".org-switcher select").selectOption("acme");
  await expect(
    page.locator(".repo-row .repo-name").filter({ hasText: "core-api" }),
  ).toBeVisible();

  await page
    .locator(".nav-panel")
    .getByRole("button", { name: /Collapse repository explorer/ })
    .click();
  await expect(page.locator(".repo-panel.collapsed")).toBeVisible();
});
