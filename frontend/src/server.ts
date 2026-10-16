import {
  createStartHandler,
  defaultStreamHandler,
} from "@tanstack/react-start/server"
import { createServerEntry } from "@tanstack/react-start/server-entry"

// Built assets are uploaded to object storage and served from a CDN when
// VITE_ASSETS_URL is set at build time (see vite.config.ts). This also points
// the preloaded route chunks in the HTML at the CDN.
const assetsUrl = import.meta.env.VITE_ASSETS_URL?.replace(/\/$/, "")

const fetch = createStartHandler(
  assetsUrl
    ? { handler: defaultStreamHandler, transformAssets: assetsUrl }
    : defaultStreamHandler,
)

export default createServerEntry({ fetch })
