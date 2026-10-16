import {
  MutationCache,
  QueryCache,
  QueryClient,
  QueryClientProvider,
} from "@tanstack/react-query"
import { createRouter } from "@tanstack/react-router"
import { createIsomorphicFn } from "@tanstack/react-start"
import { AxiosError } from "axios"
import { client } from "./client/client.gen"
import { routeTree } from "./routeTree.gen"

// The browser calls the API on its own origin (the reverse proxy routes /api to
// Django), unless VITE_API_URL points at an API on another domain. During SSR
// the server calls Django directly (e.g. http://backend:8000 in Docker Compose).
const getApiUrl = createIsomorphicFn()
  .server(
    () =>
      process.env.API_INTERNAL_URL ||
      import.meta.env.VITE_API_URL ||
      "http://localhost:8000",
  )
  .client(() => import.meta.env.VITE_API_URL ?? "")

client.setConfig({
  baseURL: getApiUrl(),
  // The token lives in the browser only: server-rendered (public) pages make
  // anonymous API calls, so one request never sees another user's token.
  auth: () =>
    typeof window === "undefined"
      ? ""
      : localStorage.getItem("access_token") || "",
})

const handleApiError = (error: Error) => {
  if (
    typeof window !== "undefined" &&
    error instanceof AxiosError &&
    [401, 403].includes(error.response?.status ?? 0)
  ) {
    localStorage.removeItem("access_token")
    window.location.href = "/login"
  }
}

export function getRouter() {
  // A new QueryClient per router, so SSR requests never share cached data
  const queryClient = new QueryClient({
    queryCache: new QueryCache({ onError: handleApiError }),
    mutationCache: new MutationCache({ onError: handleApiError }),
  })

  return createRouter({
    routeTree,
    context: { queryClient },
    scrollRestoration: true,
    Wrap: ({ children }) => (
      <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    ),
  })
}

declare module "@tanstack/react-router" {
  interface Register {
    router: ReturnType<typeof getRouter>
  }
}
