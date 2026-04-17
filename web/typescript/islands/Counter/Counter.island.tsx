import { createSignal } from "solid-js";

export function Counter({ initial }: Readonly<{ initial?: number }>) {
  const [count, setCount] = createSignal(initial ?? 0);

  return (
    <div>
      <span>Count: {count()}</span>
      <button type="button" class="m-2 border px-1" onClick={() => setCount((prev) => prev + 1)}>
        +1
      </button>
    </div>
  );
}
