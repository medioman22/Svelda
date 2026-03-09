const selectors = {
  section: ".js-product-tabs-section",
  button: ".js-product-tabs-button",
  tab: ".js-product-tabs-tab",
  slider: ".js-featured-content-slider",
  buttonsWrapper: ".js-product-tabs-buttons-wrapper"
};
const ProductTabs = () => {
  const cssClasses = window.themeCore.utils.cssClasses;
  let Slider;
  let sections = [];
  async function init(sectionId) {
    Slider = await window.themeCore.utils.getExternalUtil(
      "FeaturedContentSlider"
    );
    sections = [...document.querySelectorAll(selectors.section)].filter((section) => !sectionId || section.closest(`#shopify-section-${sectionId}`));
    sections.forEach(
      (section) => section.addEventListener("click", clickHandler)
    );
    sections.forEach((section) => {
      let sliderOptions = {
        grabCursor: true,
        slidesPerView: 2
      };
      if (section.hasAttribute("data-cards-indent")) {
        sliderOptions.spaceBetween = 10;
      }
      const tabs = [...section.querySelectorAll(selectors.tab)].filter(
        (tab) => tab.querySelector(selectors.slider)
      );
      tabs.forEach((tab) => {
        Slider(tab, sliderOptions).init();
        tab.classList.remove(cssClasses.loading);
      });
    });
  }
  function clickHandler(event) {
    const button = event.target.closest(selectors.button);
    const section = event.target.closest(selectors.section);
    if (!button || !section) {
      return;
    }
    const tabs = [...section.querySelectorAll(selectors.tab)];
    const buttons = [...section.querySelectorAll(selectors.button)];
    const index = button.dataset.index;
    const buttonsWrapper = section.querySelector(selectors.buttonsWrapper);
    if (!tabs || !index) {
      return;
    }
    tabs.forEach(
      (tab) => tab.classList.toggle(cssClasses.hidden, tab.dataset.index !== index)
    );
    buttons.forEach(
      (button2) => button2.classList.toggle(
        cssClasses.active,
        button2.dataset.index === index
      )
    );
    const newActiveOffset = button.offsetLeft;
    buttonsWrapper.scrollTo({
      left: newActiveOffset,
      behavior: "smooth"
    });
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.ProductTabs = window.themeCore.ProductTabs || ProductTabs();
  window.themeCore.utils.register(window.themeCore.ProductTabs, "product-tabs");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
