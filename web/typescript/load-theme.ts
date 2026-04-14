(() => {
  const theme = (() => {
    let theme: string | null = null;
    if (typeof localStorage !== "undefined" && localStorage.getItem("theme")) {
      theme = localStorage.getItem("theme");
    }
    if (theme === null && window.matchMedia("(prefers-color-scheme: dark)").matches) {
      return "dark";
    }
    // TODO
    // return "light"
    return "dark";
  })();

  if (theme === "light") {
    document.documentElement.classList.remove("light");
  } else if (theme === "dark") {
    document.documentElement.classList.remove("dark");
  }

  window.localStorage.setItem("theme", theme);
})();
