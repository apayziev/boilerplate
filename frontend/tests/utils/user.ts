import { expect, type Page } from "@playwright/test"

export async function signUpNewUser(
  page: Page,
  name: string,
  phone: string,
  password: string,
) {
  await page.goto("/signup")

  await page.getByTestId("full-name-input").fill(name)
  await page.getByTestId("phone-input").fill(phone)
  await page.getByTestId("password-input").fill(password)
  await page.getByTestId("confirm-password-input").fill(password)
  await page.getByRole("button", { name: "Sign Up" }).click()
  await page.goto("/login")
}

export async function logInUser(page: Page, phone: string, password: string) {
  await page.goto("/login")

  await page.getByTestId("phone-input").fill(phone)
  await page.getByTestId("password-input").fill(password)
  await page.getByRole("button", { name: "Kirish" }).click()
  await page.waitForURL("/")
  await expect(
    page.getByText("Yana ko'rishganimizdan xursandmiz!"),
  ).toBeVisible()
}

export async function logOutUser(page: Page) {
  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Chiqish" }).click()
  await page.goto("/login")
}
