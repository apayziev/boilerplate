import { expect, type Page, test } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"
import { createUser } from "./utils/privateApi.ts"
import { randomPassword, randomPhone } from "./utils/random.ts"

test.use({ storageState: { cookies: [], origins: [] } })

const fillForm = async (page: Page, phone: string, password: string) => {
  await page.getByTestId("phone-input").fill(phone)
  await page.getByTestId("password-input").fill(password)
}

const verifyInput = async (page: Page, testId: string) => {
  const input = page.getByTestId(testId)
  await expect(input).toBeVisible()
  await expect(input).toHaveText("")
  await expect(input).toBeEditable()
}

test("Inputs are visible, empty and editable", async ({ page }) => {
  await page.goto("/login")

  await verifyInput(page, "phone-input")
  await verifyInput(page, "password-input")
})

test("Log In button is visible", async ({ page }) => {
  await page.goto("/login")

  await expect(page.getByRole("button", { name: "Kirish" })).toBeVisible()
})

test("Log in with valid phone and password", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, firstSuperuser, firstSuperuserPassword)
  await page.getByRole("button", { name: "Kirish" }).click()

  await page.waitForURL("/")

  await expect(
    page.getByText("Yana ko'rishganimizdan xursandmiz!"),
  ).toBeVisible()
})

test("Log in with empty username field", async ({ page }) => {
  await page.goto("/login")

  await fillForm(page, "", firstSuperuserPassword)
  await page.getByRole("button", { name: "Kirish" }).click()

  await expect(page.getByText("Foydalanuvchi nomi yoki telefon majburiy")).toBeVisible()
})

test("Log in with invalid password", async ({ page }) => {
  const password = randomPassword()

  await page.goto("/login")
  await fillForm(page, firstSuperuser, password)
  await page.getByRole("button", { name: "Kirish" }).click()

  await expect(
    page.getByText("Foydalanuvchi nomi, telefon yoki parol noto'g'ri."),
  ).toBeVisible()
})

test("Successful log out", async ({ page }) => {
  const phone = randomPhone()
  const password = randomPassword()
  await createUser({ phone, password })

  await page.goto("/login")
  await fillForm(page, phone, password)
  await page.getByRole("button", { name: "Kirish" }).click()
  await page.waitForURL("/")
  await expect(
    page.getByText("Yana ko'rishganimizdan xursandmiz!"),
  ).toBeVisible()

  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Chiqish" }).click()
  await page.waitForURL("/login")
})

test("Logged-out user cannot access protected routes", async ({ page }) => {
  const phone = randomPhone()
  const password = randomPassword()
  await createUser({ phone, password })

  await page.goto("/login")
  await fillForm(page, phone, password)
  await page.getByRole("button", { name: "Kirish" }).click()
  await page.waitForURL("/")
  await expect(
    page.getByText("Yana ko'rishganimizdan xursandmiz!"),
  ).toBeVisible()

  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Chiqish" }).click()
  await page.waitForURL("/login")

  await page.goto("/settings")
  await page.waitForURL("/login")
})

test("Redirects to /login when not authenticated", async ({ page }) => {
  await page.goto("/settings")
  await page.waitForURL("/login")
  await expect(page).toHaveURL("/login")
})
