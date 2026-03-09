const selectors$1 = {
  galleryItem: ".js-gallery-carousel-slide",
  galleryItemsContainer: ".js-gallery-items-container"
};
const classes = {
  activeSlide: ".swiper-slide-active"
};
const Slider = async (gallery) => {
  const galleryItemsContainer = gallery.querySelector(selectors$1.galleryItemsContainer);
  let autoplaySpeed = galleryItemsContainer.getAttribute("data-autoplay-speed");
  const animationTime = 400;
  const Swiper = window.themeCore.utils.Swiper;
  const Autoplay = await window.themeCore.utils.getExternalUtil(
    "swiperAutoplay"
  );
  Swiper.use([Autoplay]);
  function debounce(func, timeout = animationTime) {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => {
        func.apply(this, args);
      }, timeout);
    };
  }
  function setContainerHeight() {
    const activeSlide = [...gallery.querySelectorAll(selectors$1.galleryItem)].find((slide) => slide.closest(classes.activeSlide));
    gallery.style.height = `${activeSlide.offsetHeight + 8}px`;
  }
  const processChange = debounce(() => setContainerHeight());
  function init() {
    const gallerySlider = new Swiper(galleryItemsContainer, {
      slidesPerView: "auto",
      centeredSlides: true,
      loop: true,
      autoplay: autoplaySpeed ? {
        delay: autoplaySpeed,
        disableOnInteraction: true
      } : false,
      pagination: {
        el: ".swiper-pagination",
        type: "bullets",
        clickable: true
      },
      navigation: {
        nextEl: ".swiper-button-next",
        prevEl: ".swiper-button-prev"
      },
      breakpoints: {
        1200: {
          autoplay: autoplaySpeed ? {
            delay: autoplaySpeed,
            disableOnInteraction: false,
            pauseOnMouseEnter: true
          } : false
        }
      },
      on: {
        init: processChange,
        slideChangeTransitionStart: processChange
      }
    });
    window.addEventListener("resize", setContainerHeight);
    gallerySlider.update();
  }
  return Object.freeze({
    init
  });
};
const selectors = {
  gallery: ".js-gallery-carousel-container"
};
const GalleryCarousel = () => {
  async function init(sectionId) {
    const galleries = [...document.querySelectorAll(selectors.gallery)].filter((section) => !sectionId || section.closest(`#shopify-section-${sectionId}`));
    galleries.forEach(async (gallery) => {
      const slider = await Slider(gallery);
      slider.init();
    });
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.GalleryCarousel = window.themeCore.GalleryCarousel || GalleryCarousel();
  window.themeCore.utils.register(window.themeCore.GalleryCarousel, "gallery-carousel");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
