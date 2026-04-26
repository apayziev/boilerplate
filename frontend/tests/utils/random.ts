/** Generate a unique +998 phone for test fixtures. */
export const randomPhone = () => {
  const tail = Math.floor(Math.random() * 1_000_000_000)
    .toString()
    .padStart(9, "0")
  return `+998${tail}`
}

export const randomTeamName = () =>
  `Team ${Math.random().toString(36).substring(7)}`

// Generates a password that satisfies backend requirements:
// 8+ chars, uppercase, lowercase, digit, special character
export const randomPassword = () => {
  const lower = Math.random().toString(36).substring(2, 8)
  return `${lower}A1!`
}

export const slugify = (text: string) =>
  text
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^\w-]+/g, "")
