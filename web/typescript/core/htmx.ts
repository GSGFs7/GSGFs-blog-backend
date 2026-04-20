import htmx from "htmx.org";
import "htmx-ext-head-support";

declare global {
  interface Window {
    htmx: typeof htmx;
  }
}

// get the csrf token has put in base.html
const getCsrfToken = (): string | null => {
  const meta = document.querySelector("meta[name='csrf-token']");
  return meta?.getAttribute("content") ?? null;
};

document.body.addEventListener("htmx:configRequest", (event) => {
  const csrfToken = getCsrfToken();
  if (!csrfToken) {
    return;
  }

  const detail = (event as CustomEvent).detail;
  detail.headers["X-CSRFToken"] = csrfToken;
});

window.htmx = htmx;
