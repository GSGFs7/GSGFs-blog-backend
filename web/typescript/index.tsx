// Do not import theme.ts here. it should be load in very early.

import "./core/htmx";
import { setupIslands } from "./core/bootstrap";
import { COMPONENTS } from "./islands";

setupIslands(COMPONENTS);
