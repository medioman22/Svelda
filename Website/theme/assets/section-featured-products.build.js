const selectors = {
  section: ".js-featured-products"
};
const FeaturedProducts = () => {
  let Swiper = window.themeCore.utils.Swiper;
  function init() {
    const sections = [...document.querySelectorAll(selectors.section)];
    sections.forEach((section) => {
      let slider = section.querySelector(".js-featured-products-slider");
      let slidesPerViewDesktop = +slider.getAttribute("data-slides-in-row") || 4;
      let sliderOptions = {
        grabCursor: true,
        slidesPerView: 2,
        pagination: {
          el: ".js-featured-products-pagination",
          clickable: true,
          bulletElement: "button"
        },
        navigation: {
          nextEl: `.js-swiper-button-next-${section.id}`,
          prevEl: `.js-swiper-button-prev-${section.id}`
        },
        breakpoints: {
          768: {
            slidesPerView: 3
          },
          1200: {
            slidesPerView: slidesPerViewDesktop
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
  window.themeCore.FeaturedProducts = window.themeCore.FeaturedProducts || FeaturedProducts();
  window.themeCore.utils.register(window.themeCore.FeaturedProducts, "featured-products");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
