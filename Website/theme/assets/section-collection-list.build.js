const selectors = {
  section: ".js-collection-list"
};
const CollectionList = () => {
  let Slider;
  const sliderOptions = {
    slidesPerView: 1.16
  };
  async function init(sectionId) {
    Slider = await window.themeCore.utils.getExternalUtil(
      "FeaturedContentSlider"
    );
    const sections = [...document.querySelectorAll(selectors.section)].filter((section) => !sectionId || section.closest(`#shopify-section-${sectionId}`));
    sections.forEach((section) => Slider(section, sliderOptions).init());
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.CollectionList = window.themeCore.CollectionList || CollectionList();
  window.themeCore.utils.register(window.themeCore.CollectionList, "collection-list");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
