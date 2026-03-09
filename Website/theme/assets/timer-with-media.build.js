const selectors = {
  section: ".js-timer-with-media",
  timer: ".js-timer"
};
const TimerWithMedia = () => {
  let Timer = window.themeCore.utils.Timer;
  function init(sectionId) {
    const sections = [...document.querySelectorAll(selectors.section)].filter((section) => !sectionId || section.closest(`#shopify-section-${sectionId}`));
    sections.forEach((section) => {
      const timers = section.querySelectorAll(selectors.timer);
      setTimeout(() => {
        timers.forEach(function(timerEl) {
          Timer(timerEl).init();
        });
      }, 0);
    });
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.TimerWithMedia = window.themeCore.TimerWithMedia || TimerWithMedia();
  window.themeCore.utils.register(window.themeCore.TimerWithMedia, "timer-with-media");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
