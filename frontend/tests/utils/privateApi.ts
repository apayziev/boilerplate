// Helper to create users for testing using admin credentials.
import { LoginService, OpenAPI, UsersService } from "../../src/client"
import { firstSuperuser, firstSuperuserPassword } from "../config"

OpenAPI.BASE = `${process.env.VITE_API_URL}`

export const createUser = async ({
  phone,
  password,
}: {
  phone: string
  password: string
}) => {
  const loginResponse = await LoginService.loginAccessToken({
    formData: {
      username: firstSuperuser,
      password: firstSuperuserPassword,
    },
  })

  const previousToken = OpenAPI.TOKEN
  OpenAPI.TOKEN = loginResponse.access_token

  try {
    return await UsersService.createUser({
      requestBody: {
        phone,
        password,
        name: "Test User",
      },
    })
  } finally {
    OpenAPI.TOKEN = previousToken
  }
}
