const selectors = {
  section: ".js-shop-the-look",
  lookSlider: ".js-shop-the-look-slider",
  lookSlide: ".js-shop-the-look-slide",
  lookThumbSlider: ".js-shop-the-look-thumb-slider",
  lookThumbSlide: ".js-shop-the-look-thumb-slide",
  productsSlider: ".js-shop-the-look-products-slider-mobile",
  productsSlide: ".js-shop-the-look-products-slide-mobile",
  productsPagination: ".js-shop-the-look-products-pagination-mobile",
  productsSliderFraction: ".js-shop-the-look-products-slider-fraction-mobile",
  lookPointButton: ".js-shop-the-look-point",
  lookPointButtonMobile: ".js-shop-the-look-point-mobile",
  productsDrawer: ".js-shop-the-look-drawer-mobile",
  productModal: ".js-shop-the-look-product-modal",
  productModalContainer: ".js-shop-the-look-product-modal-container",
  productModalClose: ".js-shop-the-look-product-modal-close"
};
const classes = {
  activeSlide: "swiper-slide-active"
};
const attributes = {
  ariaExpanded: "aria-expanded"
};
const breakpoints = {
  afterMedium: "(min-width: 1200px)"
};
const ShopTheLook = () => {
  let sectionComponents = [];
  const Swiper = window.themeCore.utils.Swiper;
  const cssClasses = window.themeCore.utils.cssClasses;
  let EffectFade;
  let MouseWheel;
  let productsCarousel;
  const Toggle = window.themeCore.utils.Toggle;
  const AFTER_MEDIUM_SCREEN = window.matchMedia(breakpoints.afterMedium);
  let isDesktop = AFTER_MEDIUM_SCREEN.matches;
  async function init(sectionId) {
    const sections = [...document.querySelectorAll(selectors.section)].filter((section) => !sectionId || section.closest(`#shopify-section-${sectionId}`));
    EffectFade = await window.themeCore.utils.getExternalUtil("swiperEffectFade");
    MouseWheel = await window.themeCore.utils.getExternalUtil("swiperMousewheel");
    Swiper.use([EffectFade, MouseWheel]);
    sections.forEach((section) => {
      sectionComponents.push({
        section,
        lookSlider: section.querySelector(selectors.lookSlider),
        lookSlides: [
          ...section.querySelectorAll(selectors.lookSlide)
        ],
        lookThumbSlider: section.querySelector(selectors.lookThumbSlider),
        lookThumbSlides: [
          ...section.querySelectorAll(selectors.lookThumbSlide)
        ],
        productsSliders: [
          ...section.querySelectorAll(selectors.productsSlider)
        ],
        productsSlides: [
          ...section.querySelectorAll(selectors.productsSlide)
        ],
        pointButtons: [
          ...section.querySelectorAll(selectors.lookPointButton)
        ],
        pointButtonsMobile: [
          ...section.querySelectorAll(selectors.lookPointButtonMobile)
        ]
      });
    });
    setEventListeners();
    setEventBusListeners();
    initSliders();
    initPointsListener();
  }
  function setEventBusListeners() {
    sectionComponents.forEach(({ lookSlides, pointButtonsMobile }) => {
      lookSlides.forEach((slide) => {
        const blockIndex = +slide.dataset.blockIndex;
        window.themeCore.EventBus.listen(["EscEvent:on", `Overlay:shopTheLookDrawerProducts-${blockIndex}:close`, `Toggle:shopTheLookDrawerProducts-${blockIndex}:close`], () => {
          removeActiveClasses(pointButtonsMobile);
        });
      });
    });
  }
  function initPointsListener() {
    sectionComponents.forEach(({ lookSlides }) => {
      lookSlides.forEach((lookSlide) => {
        const pointButton = lookSlide.querySelector(selectors.lookPointButtonMobile);
        if (!pointButton)
          return;
        const toggle = pointButton.dataset.jsToggle;
        toggle && Toggle({
          toggleSelector: toggle,
          toggleTabIndex: true,
          overlayPlacement: document.body
        }).init();
      });
    });
  }
  function setEventListeners() {
    AFTER_MEDIUM_SCREEN.addEventListener("change", handleScreenChange);
    sectionComponents.forEach(({ section }) => {
      section.addEventListener("click", pointButtonHandler);
      section.addEventListener("click", pointButtonMobileHandler);
      section.addEventListener("click", thumbButtonHandler);
      section.addEventListener("click", closeModal);
    });
  }
  function handleScreenChange(event) {
    isDesktop = event.matches;
    let lookSlidesArray;
    let blockIndex;
    let productModal;
    let pointButtons;
    let pointButtonsMobile;
    sectionComponents.forEach(({ lookSlides }) => {
      lookSlidesArray = lookSlides;
      const activeSlide = lookSlides.find((slide) => slide.classList.contains(classes.activeSlide));
      pointButtonsMobile = [...activeSlide.querySelectorAll(selectors.lookPointButtonMobile)];
      blockIndex = +activeSlide.dataset.blockIndex;
    });
    if (isDesktop) {
      window.themeCore.EventBus.emit(`Toggle:shopTheLookDrawerProducts-${blockIndex}:close`);
      removeActiveClasses(pointButtonsMobile);
    } else {
      lookSlidesArray.forEach((slide) => {
        pointButtons = [...slide.querySelectorAll(selectors.lookPointButton)];
        productModal = slide.querySelector(selectors.productModal);
        productModal.classList.remove(cssClasses.active);
        removeActiveClasses(pointButtons);
      });
      initSliders();
    }
  }
  function thumbButtonHandler(event) {
    var _a;
    const lookThumbSlide = event.target.closest(selectors.lookThumbSlide);
    if (!lookThumbSlide)
      return;
    const lookThumbSlider = lookThumbSlide.closest(selectors.lookThumbSlider);
    setCurrentSlide(lookThumbSlider.swiper, (_a = lookThumbSlide.dataset) == null ? void 0 : _a.slideIndex);
  }
  function pointButtonHandler(event) {
    const pointButton = event.target.closest(selectors.lookPointButton);
    if (!pointButton)
      return;
    togglePointButton(pointButton);
  }
  function pointButtonMobileHandler(event) {
    const pointMobileButton = event.target.closest(selectors.lookPointButtonMobile);
    if (!pointMobileButton)
      return;
    togglePointButtonMobile(pointMobileButton);
  }
  function togglePointButton(pointButton) {
    const closestMainSlide = pointButton.closest(selectors.lookSlide);
    const productIndex = +pointButton.dataset.productIndex;
    const currentPointButtons = [...closestMainSlide == null ? void 0 : closestMainSlide.querySelectorAll(selectors.lookPointButton)];
    removeActiveClasses(currentPointButtons);
    setCurrentElementActive(pointButton);
    const productModal = closestMainSlide.querySelector(selectors.productModal);
    const productModalContainers = [...productModal.querySelectorAll(selectors.productModalContainer)];
    const currentProductModalContainer = productModalContainers.find((modalContainer) => +modalContainer.dataset.productIndex === productIndex);
    const currentProductModalCloseButton = currentProductModalContainer.querySelector(selectors.productModalClose);
    productModal.classList.add(cssClasses.active);
    productModalContainers.forEach((modal) => {
      const modalCloseButton = modal.querySelector(selectors.productModalClose);
      modal.classList.remove(cssClasses.active);
      toggleAriaExpanded(modalCloseButton, false);
    });
    currentProductModalContainer.classList.add(cssClasses.active);
    toggleAriaExpanded(currentProductModalCloseButton, true);
  }
  function togglePointButtonMobile(pointButton) {
    var _a;
    const closestMainSlide = pointButton.closest(selectors.lookSlide);
    const blockIndex = +pointButton.dataset.blockIndex;
    const productIndex = +pointButton.dataset.productIndex;
    const currentPointButtons = [...closestMainSlide == null ? void 0 : closestMainSlide.querySelectorAll(selectors.lookPointButton)];
    removeActiveClasses(currentPointButtons);
    setCurrentElementActive(pointButton);
    const closestProductsSlider = (_a = sectionComponents.find(
      (section) => section.productsSliders.some((slider) => +slider.dataset.blockIndex === blockIndex)
    )) == null ? void 0 : _a.productsSliders.find((slider) => +slider.dataset.blockIndex === blockIndex);
    setCurrentSlide(closestProductsSlider.swiper, productIndex);
    productIndex === 0 && updateProductsSliderFraction(closestProductsSlider, productIndex + 1);
  }
  function closeModal(event) {
    const closeModalButton = event.target.closest(selectors.productModalClose);
    if (!closeModalButton)
      return;
    const closestMainSlide = closeModalButton.closest(selectors.lookSlide);
    const currentPointButtons = [...closestMainSlide == null ? void 0 : closestMainSlide.querySelectorAll(selectors.lookPointButton)];
    const currentModal = closestMainSlide.querySelector(selectors.productModal);
    currentModal.classList.remove(cssClasses.active);
    removeActiveClasses(currentPointButtons);
    toggleAriaExpanded(closeModalButton, false);
  }
  function toggleAriaExpanded(element, flag) {
    if (!element)
      return;
    element.setAttribute(attributes.ariaExpanded, flag);
  }
  function setCurrentSlide(slider, index) {
    slider.slideTo(index);
  }
  function removeActiveClasses(elements) {
    elements.forEach(
      (element) => element.classList.remove(cssClasses.active)
    );
  }
  function setCurrentElementActive(element) {
    element.classList.add(cssClasses.active);
  }
  function initSliders() {
    sectionComponents.forEach((section) => {
      lookSliderInit(section.lookSlider, section.lookThumbSlider);
      !isDesktop && section.productsSliders.forEach((productSlider) => {
        const productsPagination = productSlider.querySelector(selectors.productsPagination);
        productsSliderInit(productSlider, productsPagination);
      });
    });
  }
  function lookSliderInit(mainSlider, thumbSlider) {
    let thumbnailsCarousel = new Swiper(thumbSlider, {
      direction: "horizontal",
      slidesPerView: 3.65,
      spaceBetween: 8,
      watchSlidesProgress: true,
      breakpoints: {
        576: {
          direction: "horizontal",
          slidesPerView: 4
        },
        1200: {
          direction: "vertical",
          slidesPerView: "auto"
        }
      }
    });
    let mainCarousel = new Swiper(mainSlider, {
      direction: "horizontal",
      slidesPerView: 1,
      effect: "fade",
      fadeEffect: {
        crossFade: true
      },
      speed: 600,
      spaceBetween: 16,
      thumbs: {
        swiper: thumbnailsCarousel
      },
      breakpoints: {
        1200: {
          direction: "vertical"
        }
      }
    });
    mainCarousel.on("slideChange", function() {
      setCurrentSlide(thumbnailsCarousel, mainCarousel.activeIndex);
    });
  }
  function productsSliderInit(productsSlider, productsPagination) {
    productsCarousel = new Swiper(productsSlider, {
      grabCursor: true,
      slidesPerView: 1,
      spaceBetween: 16,
      pagination: {
        el: productsPagination,
        type: "bullets",
        clickable: true
      }
    });
    productsCarousel.on("slideChange", function(event) {
      updateProductsSliderFraction(productsSlider, event.activeIndex + 1);
    });
  }
  function updateProductsSliderFraction(productsSlider, index) {
    const productsDrawer = productsSlider.closest(selectors.productsDrawer);
    if (!productsDrawer)
      return;
    const productsSliderFraction = productsDrawer.querySelector(selectors.productsSliderFraction);
    if (!productsSliderFraction)
      return;
    productsSliderFraction.innerHTML = index;
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.ShopTheLook = window.themeCore.ShopTheLook || ShopTheLook();
  window.themeCore.utils.register(window.themeCore.ShopTheLook, "shop-the-look");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
