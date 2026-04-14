import { createSignal } from "solid-js";

export default function Counter() {
  const [count, setCount] = createSignal(0);

  return (
    <div>
      <span>Count: {count()}</span>
      <button type="button" class="m-2 border px-1" onClick={() => setCount((prev) => prev + 1)}>
        +1
      </button>
    </div>
  );
}
