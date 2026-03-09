const CountdownBanner = () => {
  let Timer;
  let sections;
  const selectors = {
    section: ".js-countdown-banner",
    timer: ".js-timer"
  };
  function init(sectionId) {
    Timer = window.themeCore.utils.Timer;
    sections = [...document.querySelectorAll(selectors.section)].filter((section) => !sectionId || section.closest(`#shopify-section-${sectionId}`));
    sections.forEach((section) => {
      const timer = section.querySelector(selectors.timer);
      Timer(timer).init();
    });
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.CountdownBanner = window.themeCore.CountdownBanner || CountdownBanner();
  window.themeCore.utils.register(window.themeCore.CountdownBanner, "countdown-banner");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
