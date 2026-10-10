const rail = document.querySelector(".projects-rail");
const hint = document.querySelector(".projects-page__scroll-hint");

if (rail && hint) {
  function updateHint() {
    hint.hidden = rail.scrollWidth <= rail.clientWidth + 1;
  }

  updateHint();
  const observer = new ResizeObserver(updateHint);
  observer.observe(rail);
}
