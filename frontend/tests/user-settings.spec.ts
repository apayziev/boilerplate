import { expect, test } from "@playwright/test"
import { createUser } from "./utils/privateApi.ts"
import { randomPassword, randomPhone } from "./utils/random"
import { logInUser, logOutUser } from "./utils/user"

const tabs = ["Profilim", "Parol", "Xavfli zona"]

// User Information

test("My profile tab is active by default", async ({ page }) => {
  await page.goto("/settings")
  await expect(page.getByRole("tab", { name: "Profilim" })).toHaveAttribute(
    "aria-selected",
    "true",
  )
})

test("All tabs are visible", async ({ page }) => {
  await page.goto("/settings")
  for (const tab of tabs) {
    await expect(page.getByRole("tab", { name: tab })).toBeVisible()
  }
})

test.describe("Edit user full name and phone successfully", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Edit user name with a valid name", async ({ page }) => {
    const phone = randomPhone()
    const updatedName = "Test User 2"
    const password = randomPassword()

    await createUser({ phone, password })
    await logInUser(page, phone, password)

    await page.goto("/settings")
    await page.getByRole("tab", { name: "Profilim" }).click()
    await page.getByRole("button", { name: "Tahrirlash" }).click()
    await page.getByLabel("To'liq ism").fill(updatedName)
    await page.getByRole("button", { name: "Saqlash" }).click()
    await expect(page.getByText("Foydalanuvchi muvaffaqiyatli yangilandi")).toBeVisible()
    await expect(
      page.locator("form").getByText(updatedName, { exact: true }),
    ).toBeVisible()
  })

  test("Edit user phone with a valid phone", async ({ page }) => {
    const phone = randomPhone()
    const updatedPhone = randomPhone()
    const password = randomPassword()

    await createUser({ phone, password })
    await logInUser(page, phone, password)

    await page.goto("/settings")
    await page.getByRole("tab", { name: "Profilim" }).click()
    await page.getByRole("button", { name: "Tahrirlash" }).click()
    await page.getByLabel("Telefon").fill(updatedPhone)
    await page.getByRole("button", { name: "Saqlash" }).click()
    await expect(page.getByText("Foydalanuvchi muvaffaqiyatli yangilandi")).toBeVisible()
    await expect(
      page.locator("form").getByText(updatedPhone, { exact: true }),
    ).toBeVisible()
  })
})

test.describe("Edit user with invalid data", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Edit user phone with an invalid phone", async ({ page }) => {
    const phone = randomPhone()
    const password = randomPassword()
    const invalidPhone = "12345"

    await createUser({ phone, password })
    await logInUser(page, phone, password)

    await page.goto("/settings")
    await page.getByRole("tab", { name: "Profilim" }).click()
    await page.getByRole("button", { name: "Tahrirlash" }).click()
    await page.getByLabel("Telefon").fill(invalidPhone)
    await page.locator("body").click()
    await expect(
      page.getByText("Telefon +998XXXXXXXXX formatida bo'lishi kerak"),
    ).toBeVisible()
  })

  test("Cancel edit action restores original name", async ({ page }) => {
    const phone = randomPhone()
    const password = randomPassword()
    const updatedName = "Test User"

    const user = await createUser({ phone, password })
    await logInUser(page, phone, password)

    await page.goto("/settings")
    await page.getByRole("tab", { name: "Profilim" }).click()
    await page.getByRole("button", { name: "Tahrirlash" }).click()
    await page.getByLabel("To'liq ism").fill(updatedName)
    await page.getByRole("button", { name: "Bekor qilish" }).first().click()
    await expect(
      page.locator("form").getByText(user.name as string, { exact: true }),
    ).toBeVisible()
  })

  test("Cancel edit action restores original phone", async ({ page }) => {
    const phone = randomPhone()
    const password = randomPassword()
    const updatedPhone = randomPhone()

    await createUser({ phone, password })
    await logInUser(page, phone, password)

    await page.goto("/settings")
    await page.getByRole("tab", { name: "Profilim" }).click()
    await page.getByRole("button", { name: "Tahrirlash" }).click()
    await page.getByLabel("Telefon").fill(updatedPhone)
    await page.getByRole("button", { name: "Bekor qilish" }).first().click()
    await expect(
      page.locator("form").getByText(phone, { exact: true }),
    ).toBeVisible()
  })
})

// Change Password

test.describe("Change password successfully", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Update password successfully", async ({ page }) => {
    const phone = randomPhone()
    const password = randomPassword()
    const NewPassword = randomPassword()

    await createUser({ phone, password })
    await logInUser(page, phone, password)

    await page.goto("/settings")
    await page.getByRole("tab", { name: "Parol" }).click()
    await page.getByTestId("current-password-input").fill(password)
    await page.getByTestId("new-password-input").fill(NewPassword)
    await page.getByTestId("confirm-password-input").fill(NewPassword)
    await page.getByRole("button", { name: "Parolni yangilash" }).click()
    await expect(page.getByText("Parol muvaffaqiyatli yangilandi")).toBeVisible()

    await logOutUser(page)
    await logInUser(page, phone, NewPassword)
  })
})

test.describe("Change password with invalid data", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("Update password with weak passwords", async ({ page }) => {
    const phone = randomPhone()
    const password = randomPassword()
    const weakPassword = "weak"

    await createUser({ phone, password })
    await logInUser(page, phone, password)

    await page.goto("/settings")
    await page.getByRole("tab", { name: "Parol" }).click()
    await page.getByTestId("current-password-input").fill(password)
    await page.getByTestId("new-password-input").fill(weakPassword)
    await page.getByTestId("confirm-password-input").fill(weakPassword)
    await page.getByRole("button", { name: "Parolni yangilash" }).click()
    await expect(
      page.getByText("Parol kamida 8 ta belgidan iborat bo'lishi kerak"),
    ).toBeVisible()
  })

  test("New password and confirmation password do not match", async ({
    page,
  }) => {
    const phone = randomPhone()
    const password = randomPassword()
    const newPassword = randomPassword()
    const confirmPassword = randomPassword()

    await createUser({ phone, password })
    await logInUser(page, phone, password)

    await page.goto("/settings")
    await page.getByRole("tab", { name: "Parol" }).click()
    await page.getByTestId("current-password-input").fill(password)
    await page.getByTestId("new-password-input").fill(newPassword)
    await page.getByTestId("confirm-password-input").fill(confirmPassword)
    await page.getByRole("button", { name: "Parolni yangilash" }).click()
    await expect(page.getByText("Parollar mos emas")).toBeVisible()
  })

  test("Current password and new password are the same", async ({ page }) => {
    const phone = randomPhone()
    const password = randomPassword()

    await createUser({ phone, password })
    await logInUser(page, phone, password)

    await page.goto("/settings")
    await page.getByRole("tab", { name: "Parol" }).click()
    await page.getByTestId("current-password-input").fill(password)
    await page.getByTestId("new-password-input").fill(password)
    await page.getByTestId("confirm-password-input").fill(password)
    await page.getByRole("button", { name: "Parolni yangilash" }).click()
    await expect(
      page.getByText("Yangi parol joriy paroldan farq qilishi kerak"),
    ).toBeVisible()
  })
})

// Appearance

test("Appearance button is visible in sidebar", async ({ page }) => {
  await page.goto("/settings")
  await expect(page.getByTestId("theme-button")).toBeVisible()
})

test("User can switch between theme modes", async ({ page }) => {
  await page.goto("/settings")

  await page.getByTestId("theme-button").click()
  await page.getByTestId("dark-mode").click()
  await expect(page.locator("html")).toHaveClass(/dark/)

  await expect(page.getByTestId("dark-mode")).not.toBeVisible()

  await page.getByTestId("theme-button").click()
  await page.getByTestId("light-mode").click()
  await expect(page.locator("html")).toHaveClass(/light/)
})

test.describe("Selected mode is preserved across sessions", () => {
  test.use({ storageState: { cookies: [], origins: [] } })

  test("test", async ({ page }) => {
    const phone = randomPhone()
    const password = randomPassword()
    await createUser({ phone, password })
    await logInUser(page, phone, password)

    await page.goto("/settings")

    await page.getByTestId("theme-button").click()
    if (
      await page.evaluate(() =>
        document.documentElement.classList.contains("dark"),
      )
    ) {
      await page.getByTestId("light-mode").click()
      await page.getByTestId("theme-button").click()
    }

    const isLightMode = await page.evaluate(() =>
      document.documentElement.classList.contains("light"),
    )
    expect(isLightMode).toBe(true)

    await page.getByTestId("theme-button").click()
    await page.getByTestId("dark-mode").click()
    let isDarkMode = await page.evaluate(() =>
      document.documentElement.classList.contains("dark"),
    )
    expect(isDarkMode).toBe(true)

    await logOutUser(page)
    await logInUser(page, phone, password)

    isDarkMode = await page.evaluate(() =>
      document.documentElement.classList.contains("dark"),
    )
    expect(isDarkMode).toBe(true)
  })
})
