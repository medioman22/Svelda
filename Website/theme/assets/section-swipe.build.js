const Swipe$1 = () => {
  const selectors2 = {
    section: ".js-swipe",
    slider: ".js-swipe-slider"
  };
  const Swiper = window.themeCore.utils.Swiper;
  let sections = [];
  function init() {
    sections = [...document.querySelectorAll(selectors2.section)];
    sections.forEach((section) => {
      const slider = section.querySelector(selectors2.slider);
      if (!slider)
        return;
      initSlider(slider);
    });
  }
  function initSlider(slider) {
    const options = {
      direction: "horizontal",
      slidesPerView: 1,
      slidesPerGroup: 1,
      spaceBetween: 16,
      speed: 1e3,
      noSwiping: false,
      simulateTouch: true,
      mousewheel: {
        enabled: false,
        releaseOnEdges: false,
        forceToAxis: false
      },
      breakpoints: {
        1200: {
          direction: "vertical",
          noSwiping: true,
          simulateTouch: false,
          mousewheel: {
            enabled: true,
            releaseOnEdges: true,
            forceToAxis: true
          }
        }
      }
    };
    new Swiper(slider, options);
  }
  return Object.freeze({
    init
  });
};
const selectors = {
  section: ".js-swipe"
};
const Swipe = () => {
  function init(sectionId) {
    const sections = [...document.querySelectorAll(selectors.section)].filter((section) => !sectionId || section.closest(`#shopify-section-${sectionId}`));
    sections.forEach((section) => Swipe$1().init());
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.Swipe = window.themeCore.Swipe || Swipe();
  window.themeCore.utils.register(window.themeCore.Swipe, "swipe");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
