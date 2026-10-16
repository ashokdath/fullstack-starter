import { Link } from "@tanstack/react-router"

import { cn } from "@/lib/utils"
import icon from "/assets/images/fastapi-icon.svg"
import iconLight from "/assets/images/fastapi-icon-light.svg"
import logo from "/assets/images/fastapi-logo.svg"
import logoLight from "/assets/images/fastapi-logo-light.svg"

interface LogoProps {
  variant?: "full" | "icon" | "responsive"
  className?: string
  asLink?: boolean
  to?: "/" | "/dashboard"
}

// Both theme versions are rendered and toggled with the `dark:` CSS variant,
// so server-rendered HTML matches the browser whatever the saved theme is.
function ThemedImage({
  light,
  dark,
  className,
}: {
  light: string
  dark: string
  className?: string
}) {
  return (
    <>
      <img src={light} alt="FastAPI" className={cn("dark:hidden", className)} />
      <img
        src={dark}
        alt="FastAPI"
        className={cn("hidden dark:inline", className)}
      />
    </>
  )
}

export function Logo({
  variant = "full",
  className,
  asLink = true,
  to = "/",
}: LogoProps) {
  const content =
    variant === "responsive" ? (
      <>
        <span className="group-data-[collapsible=icon]:hidden">
          <ThemedImage
            light={logo}
            dark={logoLight}
            className={cn("h-6 w-auto", className)}
          />
        </span>
        <span className="hidden group-data-[collapsible=icon]:block">
          <ThemedImage
            light={icon}
            dark={iconLight}
            className={cn("size-5", className)}
          />
        </span>
      </>
    ) : (
      <ThemedImage
        light={variant === "full" ? logo : icon}
        dark={variant === "full" ? logoLight : iconLight}
        className={cn(variant === "full" ? "h-6 w-auto" : "size-5", className)}
      />
    )

  if (!asLink) {
    return content
  }

  return <Link to={to}>{content}</Link>
}
