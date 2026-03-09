const Slider = async (reviewsContainer) => {
  let autoplaySpeed = reviewsContainer.getAttribute("data-autoplay-speed");
  let layout = reviewsContainer.getAttribute("data-layout");
  let slidesToView = reviewsContainer.getAttribute("data-slides-per-view") || 3;
  let slidesToView_768 = 2;
  if (layout === "big-image") {
    slidesToView_768 = 1;
  }
  const Swiper = window.themeCore.utils.Swiper;
  const Autoplay = await window.themeCore.utils.getExternalUtil("swiperAutoplay");
  Swiper.use([Autoplay]);
  function init() {
    const reviewsSlider = new Swiper(reviewsContainer, {
      slidesPerView: 1,
      loop: true,
      spaceBetween: 16,
      autoplay: autoplaySpeed ? {
        delay: autoplaySpeed
      } : false,
      pagination: {
        el: ".swiper-pagination",
        type: "bullets",
        bulletElement: "button",
        clickable: true
      },
      breakpoints: {
        768: {
          slidesPerView: slidesToView_768
        },
        1200: {
          slidesPerView: slidesToView
        }
      }
    });
    reviewsSlider.update();
  }
  return Object.freeze({
    init
  });
};
const selectors = {
  reviews: ".js-reviews-container"
};
const Reviews = () => {
  async function init(sectionId) {
    const reviewsContainers = [
      ...document.querySelectorAll(selectors.reviews)
    ].filter((section) => !sectionId || section.closest(`#shopify-section-${sectionId}`));
    reviewsContainers.forEach(async (reviewsContainer) => {
      const slider = await Slider(reviewsContainer);
      slider.init();
    });
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.Reviews = window.themeCore.Reviews || Reviews();
  window.themeCore.utils.register(window.themeCore.Reviews, "reviews");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
