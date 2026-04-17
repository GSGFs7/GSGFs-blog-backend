// compile this file with ssr mode.

import { renderToString } from "solid-js/web";
import { SSR_COMPONENTS } from "./islands/ssr_registry";

type Props = Record<string, unknown>;

export function renderIslands(name: string, props: Props = {}) {
  const Component = SSR_COMPONENTS[name as keyof typeof SSR_COMPONENTS];
  if (!Component) {
    throw new Error(`Unknown SSR component: ${name}`);
  }
  return renderToString(() => <Component {...props} />);
}
