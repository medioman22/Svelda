const selectors = {
  slider: ".js-collection-list-tiny-container"
};
const CollectionListTiny = () => {
  let Swiper = window.themeCore.utils.Swiper;
  function init() {
    const sliders = [...document.querySelectorAll(selectors.slider)];
    sliders.forEach((slider) => {
      const sliderWidthLayout = slider.getAttribute("data-layout");
      let sliderOptions = {
        slidesPerView: 2.7,
        navigation: {
          nextEl: `.js-collection-list-tiny-button-next`,
          prevEl: `.js-collection-list-tiny-button-prev`
        },
        breakpoints: {
          576: {
            slidesPerView: 4.7
          },
          992: {
            slidesPerView: sliderWidthLayout === "slider-full" ? 6 : 4,
            spaceBetween: 16
          },
          1200: {
            slidesPerView: sliderWidthLayout === "slider-full" ? 8 : 4,
            spaceBetween: 16
          },
          1500: {
            slidesPerView: sliderWidthLayout === "slider-full" ? 10 : 4,
            spaceBetween: 16
          }
        }
      };
      new Swiper(slider, sliderOptions);
    });
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.CollectionListTiny = window.themeCore.CollectionListTiny || CollectionListTiny();
  window.themeCore.utils.register(window.themeCore.CollectionListTiny, "collection-list-with-banner");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  if (window.themeCore && window.themeCore.loaded) {
    action();
  } else {
    document.addEventListener("theme:all:loaded", action, { once: true });
  }
}
