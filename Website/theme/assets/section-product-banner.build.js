const selectors = {
  section: ".js-product-banner",
  productsSlider: ".js-product-banner-slider",
  sliderButtonNext: ".js-product-banner-slider-button-next",
  sliderButtonPrev: ".js-product-banner-slider-button-prev",
  sliderPagination: ".js-product-banner-pagination"
};
const ProductBanner = () => {
  const Swiper = window.themeCore.utils.Swiper;
  let sectionComponents = [];
  const Pagination = window.themeCore.utils.swiperPagination;
  let EffectFade;
  async function init(sectionId) {
    EffectFade = await window.themeCore.utils.getExternalUtil("swiperEffectFade");
    Swiper.use([EffectFade, Pagination]);
    const sections = [...document.querySelectorAll(selectors.section)].filter((section) => !sectionId || section.closest(`#shopify-section-${sectionId}`));
    if (sections) {
      sections.forEach((section) => {
        sectionComponents.push({
          section,
          productsSlider: section.querySelector(selectors.productsSlider),
          sliderButtonNext: section.querySelector(selectors.sliderButtonNext),
          sliderButtonPrev: section.querySelector(selectors.sliderButtonPrev),
          sliderPagination: section.querySelector(selectors.sliderPagination)
        });
      });
    }
    slidersInit();
  }
  function slidersInit() {
    sectionComponents.forEach((section) => {
      const slider = section.productsSlider;
      const buttonNext = section.sliderButtonNext;
      const buttonPrev = section.sliderButtonPrev;
      const pagination = section.sliderPagination;
      sliderInit(slider, buttonNext, buttonPrev, pagination);
    });
  }
  function sliderInit(slider, buttonNext, buttonPrev, pagination) {
    return new Swiper(slider, {
      slidesPerView: 1,
      slidesPerGroup: 1,
      speed: 600,
      effect: "fade",
      fadeEffect: {
        crossFade: true
      },
      autoHeight: true,
      pagination: {
        el: pagination,
        type: "bullets",
        clickable: true
      },
      navigation: {
        nextEl: buttonNext,
        prevEl: buttonPrev
      }
    });
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.ProductBanner = window.themeCore.ProductBanner || ProductBanner();
  window.themeCore.utils.register(window.themeCore.ProductBanner, "product-banner");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
