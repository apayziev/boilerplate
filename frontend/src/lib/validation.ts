import { z } from "zod"

// Mirror the limits enforced by the backend (see `backend/app/schemas/users.py`).
// Keep these in sync when tightening or relaxing rules on either side.
export const PASSWORD_MIN_LENGTH = 8
export const NAME_MIN_LENGTH = 2
export const NAME_MAX_LENGTH = 30
export const USERNAME_MIN_LENGTH = 2
export const USERNAME_MAX_LENGTH = 20
export const USERNAME_PATTERN = /^[a-z0-9]+$/

const PASSWORD_TOO_SHORT = `Password must be at least ${PASSWORD_MIN_LENGTH} characters`

/** Required password field (sign-up / new password). */
export const passwordSchema = z
  .string()
  .min(1, { message: "Password is required" })
  .min(PASSWORD_MIN_LENGTH, { message: PASSWORD_TOO_SHORT })

/** Optional password field (admin edit form: empty = "don't change"). */
export const optionalPasswordSchema = z
  .string()
  .min(PASSWORD_MIN_LENGTH, { message: PASSWORD_TOO_SHORT })
  .optional()
  .or(z.literal(""))

export const emailSchema = z.email({ message: "Invalid email address" })

export const optionalNameSchema = z.string().max(NAME_MAX_LENGTH).optional()
