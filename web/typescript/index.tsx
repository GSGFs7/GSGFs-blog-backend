// similar to Astro.js, a jsx component is an JS island

import type { Component as SolidComponent } from "solid-js";
import { render } from "solid-js/web";

// use dynamic import. avoid js size too large
const COMPONENTS: Record<string, () => Promise<SolidComponent<ComponentProps>>> = {
  Counter: async () => (await import("./components/Counter")).default,
} as const;

type ComponentName = keyof typeof COMPONENTS;
type ComponentProps = Record<string, unknown>;
type IslandElement = HTMLElement & {
  __solidDispose__?: () => void;
  __solidMounting__?: boolean; // avoid concurrency issues
};

function parseProps(componentName: ComponentName, propsJSON: string | null): ComponentProps {
  try {
    return JSON.parse(propsJSON ?? "{}") as ComponentProps;
  } catch (error) {
    console.error(`Failed to parse props for ${componentName}:`, error);
    return {};
  }
}

// mount solid component
async function mountIsland(element: IslandElement): Promise<void> {
  if (element.__solidDispose__ || element.__solidMounting__) {
    // avoid duplicate mounting
    return;
  }
  // take it
  element.__solidMounting__ = true;

  try {
    // get the component
    const componentName = element.getAttribute("data-solid-component") as ComponentName;
    const loadComponent = COMPONENTS[componentName];
    if (!loadComponent) {
      console.warn(`Solid component '${componentName}' not found in registry.`);
      return;
    }
    const Component = await loadComponent();

    // get component props
    const props = parseProps(componentName, element.getAttribute("data-props"));
    // render
    element.__solidDispose__ = render(() => <Component {...props} />, element);
  } finally {
    delete element.__solidMounting__;
  }
}

export function bootstrap(root: ParentNode = document) {
  root.querySelectorAll("[data-solid-component]").forEach((element) => {
    void mountIsland(element as IslandElement);
  });
}

export function cleanup(root: ParentNode) {
  root.querySelectorAll("[data-solid-component]").forEach((element) => {
    const island = element as IslandElement;
    island.__solidDispose__?.();
    delete island.__solidDispose__;
    delete island.__solidMounting__;
  });
}

function handleBeforeSwap(event: Event) {
  const target = event.target;
  if (target instanceof HTMLElement) {
    cleanup(target);
  }
}

function handleAfterSwap(event: Event) {
  const target = event.target;
  if (target instanceof HTMLElement) {
    bootstrap(target);
  }
}

// init
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => bootstrap());
} else {
  bootstrap();
}

// re-render when htmx update
document.body.addEventListener("htmx:beforeSwap", handleBeforeSwap);
document.body.addEventListener("htmx:afterSwap", handleAfterSwap);
