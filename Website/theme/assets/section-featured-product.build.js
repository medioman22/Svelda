import { P as ProductCarousel, a as ProductStickyForm, b as ProductMediaScroller, c as ProductForm } from "./product-sticky-form-e1f0721f.js";
import "./disableTabulationOnNotActiveSlidesWithModel-38e80234.js";
const FeaturedProductSection = (section) => {
  const Toggle2 = window.themeCore.utils.Toggle;
  const isElementInViewport = window.themeCore.utils.isElementInViewport;
  const off = window.themeCore.utils.off;
  const on = window.themeCore.utils.on;
  const cssClasses = window.themeCore.utils.cssClasses;
  const selectors2 = {
    mediaContainer: ".js-product-media-container",
    thumbnailsStacked: ".js-product-media-thumbnails-stacked",
    thumbnailsSlide: ".js-product-media-thumbnails-slide",
    slide: ".js-product-gallery-slide",
    modelButton: ".js-product-media-model-button",
    modelPoster: ".js-product-media-model-poster",
    modelContent: ".js-product-media-model-content"
  };
  const sectionId = section && section.dataset.sectionId;
  const carouselSelectors = {
    slider: `.js-product-media-slider-${sectionId}`,
    sliderNavigationNext: `.js-product-media-slider-next-${sectionId}`,
    sliderNavigationPrev: `.js-product-media-slider-prev-${sectionId}`,
    thumbNavigationNext: `.js-product-media-thumb-next-${sectionId}`,
    thumbNavigationPrev: `.js-product-media-thumb-prev-${sectionId}`,
    sliderSlideVariantId: `.js-product-gallery-slide-variant-${sectionId}`,
    sliderThumbnails: `.js-product-media-slider-thumbnails-${sectionId}`,
    sliderPagination: `.product-media__slider-pagination-${sectionId}`
  };
  const mediaContainerClasses = {
    stacked: "product-media--layout-stacked",
    stacked_2_col: "product-media--layout-stacked_2_col",
    stacked_2_col_with_big_img: "product-media--layout-stacked_2_col_with_big_image",
    slider: "product-media--layout-carousel"
  };
  const drawersSelectors = {
    sizeGuideDrawer: `productSizeGuideDrawer-${sectionId}`,
    descriptionDrawer: `descriptionDrawer-${sectionId}`,
    customDrawer1: `productDrawer1-${sectionId}`,
    customDrawer2: `productDrawer2-${sectionId}`,
    customDrawer3: `productDrawer3-${sectionId}`,
    customDrawer4: `productDrawer4-${sectionId}`
  };
  let Carousel = null;
  function init2() {
    Carousel = ProductCarousel({
      selectors: carouselSelectors,
      sectionId
    });
    const productStickyForms = ProductStickyForm(section);
    productStickyForms.init();
    initCarousel();
    setDrawers();
    initModelButtons();
    const productHandle = section.dataset.productHandle;
    if (!productHandle) {
      return;
    }
    let recentlyViewed = localStorage.getItem("theme_recently_viewed");
    if (recentlyViewed) {
      try {
        recentlyViewed = JSON.parse(recentlyViewed);
        recentlyViewed = [.../* @__PURE__ */ new Set([...recentlyViewed, productHandle])];
        recentlyViewed = recentlyViewed.slice(-11);
        localStorage.setItem("theme_recently_viewed", JSON.stringify(recentlyViewed));
      } catch (e) {
        console.log(e);
      } finally {
        return;
      }
    }
    localStorage.setItem("theme_recently_viewed", `["${productHandle}"]`);
  }
  function initCarousel() {
    const mediaContainer = section.querySelector(selectors2.mediaContainer);
    if (!mediaContainer) {
      return;
    }
    const mediaLayout = mediaContainer.dataset.mediaLayout;
    if (!mediaLayout) {
      return;
    }
    if (mediaLayout === "carousel") {
      Carousel.init();
    }
    if (mediaLayout === "stacked" || mediaLayout === "stacked_2_col" || mediaLayout === "stacked_2_col_with_big_image") {
      updateMedia();
      on("scroll", document, onScroll);
      activeDragThumbnail();
      on("resize", updateMedia);
      ProductMediaScroller(section).init();
    }
  }
  function updateMedia() {
    const mediaContainer = section.querySelector(selectors2.mediaContainer);
    if (!mediaContainer) {
      return;
    }
    const mediaLayout = mediaContainer.dataset.mediaLayout;
    let stackedClass = mediaContainerClasses.stacked;
    if (mediaLayout === "stacked_2_col") {
      stackedClass = mediaContainerClasses.stacked_2_col;
    } else if (mediaLayout === "stacked_2_col_with_big_image") {
      stackedClass = mediaContainerClasses.stacked_2_col_with_big_img;
    }
    if (window.innerWidth > 1199) {
      Carousel.destroy();
      mediaContainer.classList.add(stackedClass);
      mediaContainer.classList.remove(mediaContainerClasses.slider);
    } else {
      Carousel.init();
      mediaContainer.classList.add(mediaContainerClasses.slider);
      mediaContainer.classList.remove(stackedClass);
    }
  }
  function onScroll() {
    off("scroll", document, onScroll);
    const mediaContainer = section.querySelector(selectors2.mediaContainer);
    const thumbnailsStacked = section.querySelector(selectors2.thumbnailsStacked);
    if (!mediaContainer || !thumbnailsStacked) {
      return;
    }
    const slides = [...mediaContainer.querySelectorAll(selectors2.slide)];
    slides.forEach((slide) => {
      setTimeout(() => {
        if (isElementInViewport(slide, thumbnailsStacked, 200)) {
          const thumbnails = [...thumbnailsStacked.querySelectorAll(selectors2.thumbnailsSlide)];
          thumbnails.forEach((thumbnail) => {
            thumbnail.classList.remove(cssClasses.active);
          });
          const currentThumbnail = thumbnails.find((thumbnail) => thumbnail.dataset.mediaId === slide.dataset.mediaId);
          if (currentThumbnail) {
            currentThumbnail.classList.add(cssClasses.active);
            const offsetTopThumbnail = currentThumbnail.offsetTop;
            const offsetHeightContainer = thumbnailsStacked.offsetHeight / 2;
            const offsetHeightThumbnail = currentThumbnail.offsetHeight / 2;
            const scroll = offsetTopThumbnail - offsetHeightContainer + offsetHeightThumbnail;
            thumbnailsStacked.scroll(0, scroll);
          }
        }
        on("scroll", document, onScroll);
      }, 700);
    });
  }
  function activeDragThumbnail() {
    const thumbnail = section.querySelector(selectors2.thumbnailsStacked);
    if (!thumbnail) {
      return;
    }
    let pos = { top: 0, left: 0, x: 0, y: 0 };
    let isDrag = false;
    const mouseDownHandler = function(e) {
      thumbnail.style.cursor = "grabbing";
      thumbnail.style.userSelect = "none";
      thumbnail.style.scrollBehavior = "auto";
      pos = {
        left: thumbnail.scrollLeft,
        top: thumbnail.scrollTop,
        // Get the current mouse position
        x: e.clientX,
        y: e.clientY
      };
      on("mousemove", document, mouseMoveHandler);
      on("mouseup", document, mouseUpHandler);
    };
    const mouseMoveHandler = function(e) {
      const dx = e.clientX - pos.x;
      const dy = e.clientY - pos.y;
      isDrag = Boolean(dx + dy);
      thumbnail.scrollTop = pos.top - dy;
      thumbnail.scrollLeft = pos.left - dx;
    };
    const mouseUpHandler = function() {
      const anchors = [...thumbnail.querySelectorAll("a")];
      if (anchors && isDrag) {
        const preventDefault = (e) => {
          e.preventDefault();
          anchors.forEach((anchor) => {
            off("click", anchor, preventDefault);
          });
          isDrag = false;
        };
        anchors.forEach((anchor) => {
          on("click", anchor, preventDefault);
        });
      }
      document.removeEventListener("mousemove", mouseMoveHandler);
      document.removeEventListener("mouseup", mouseUpHandler);
      thumbnail.style.cursor = "grab";
      thumbnail.style.removeProperty("user-select");
      thumbnail.style.scrollBehavior = "smooth";
    };
    on("mousedown", thumbnail, mouseDownHandler);
  }
  function setDrawers() {
    try {
      setToggleDrawer(drawersSelectors.sizeGuideDrawer, { hasFullWidth: true });
      setToggleDrawer(drawersSelectors.descriptionDrawer);
      setToggleDrawer(drawersSelectors.customDrawer1);
      setToggleDrawer(drawersSelectors.customDrawer2);
      setToggleDrawer(drawersSelectors.customDrawer3);
      setToggleDrawer(drawersSelectors.customDrawer4);
    } catch (e) {
    }
  }
  function setToggleDrawer(selector, options = {}) {
    const toggleButton = document.querySelector(`[data-js-toggle="${selector}"]`);
    if (!toggleButton) {
      return;
    }
    const ToggleDrawer = Toggle2({
      toggleSelector: selector,
      ...options
    });
    ToggleDrawer.init();
    if (selector === drawersSelectors.sizeGuideDrawer) {
      let sizeGuideDrawer = document.getElementById(drawersSelectors.sizeGuideDrawer);
      if (!sizeGuideDrawer) {
        return;
      }
      on("click", sizeGuideDrawer, function(e) {
        if (e.target == this) {
          ToggleDrawer.close(sizeGuideDrawer);
        }
      });
    }
  }
  function initModelButtons() {
    const modelButtons = [...section.querySelectorAll(selectors2.modelButton)];
    if (!modelButtons.length) {
      return;
    }
    section.addEventListener("click", (event) => {
      const button = event.target.closest(selectors2.modelButton);
      if (!button) {
        return;
      }
      const container = button.parentElement;
      const poster = container.querySelector(selectors2.modelPoster);
      const content = container.querySelector(selectors2.modelContent);
      if (!poster || !content) {
        return;
      }
      poster.remove();
      button.remove();
      content.classList.remove(cssClasses.hidden);
      Carousel.disableSwipe();
    });
  }
  return Object.freeze({
    init: init2
  });
};
const selectors = {
  section: '[data-section-type="product"]',
  productAvailabilityToggleSelector: "[data-js-toggle-selector]",
  video: ".js-video",
  slide: ".js-product-gallery-slide"
};
const videos = [];
let sections;
let ProductForms;
let Toggle;
let Video;
function init(sectionId) {
  Toggle = window.themeCore.utils.Toggle;
  sections = [...document.querySelectorAll(selectors.section)].filter((section) => !sectionId || section.closest(`#shopify-section-${sectionId}`));
  ProductForms = ProductForm();
  sections.forEach(initSection);
  ProductForms.init();
  Video = window.themeCore.utils.Video;
  initVideos();
  setEventBusListeners();
  window.themeCore.EventBus.emit("product:loaded");
}
function initSection(section) {
  const productSection = FeaturedProductSection(section);
  window.themeCore.EventBus.listen(
    `pickup-availability-drawer:productAvailability-pickup-availability__${section.dataset.sectionId}:loaded`,
    () => {
      const productAvailabilityToggles = [
        ...document.querySelectorAll(
          selectors.productAvailabilityToggleSelector
        )
      ];
      const productAvailabilityToggle = productAvailabilityToggles.find(
        (toggle) => {
          return toggle.dataset.jsToggle === `productAvailability-pickup-availability__${section.dataset.sectionId}`;
        }
      );
      const productAvailability = Toggle({
        toggleSelector: productAvailabilityToggle.dataset.target
      });
      productAvailability.init();
    }
  );
  productSection.init();
}
function onProductSliderSlideChange() {
  if (!videos.length) {
    window.themeCore.EventBus.remove("product-slider:slide-change", onProductSliderSlideChange);
  }
  videos.forEach(({ player }) => {
    try {
      player.pauseVideo();
    } catch (e) {
    }
    try {
      player.pause();
    } catch (e) {
    }
  });
}
function setEventBusListeners() {
  window.themeCore.EventBus.listen("product-slider:slide-change", onProductSliderSlideChange);
}
async function initVideos() {
  const slides = [...document.querySelectorAll(selectors.slide)];
  slides.forEach((slide) => {
    const [video] = Video({
      videoContainer: slide,
      options: {
        youtube: {
          controls: 1,
          showinfo: 1
        }
      }
    }).init();
    if (video) {
      videos.push(video);
    }
  });
}
const FeaturedProduct = () => {
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.FeaturedProduct = window.themeCore.FeaturedProduct || FeaturedProduct();
  window.themeCore.utils.register(window.themeCore.FeaturedProduct, "featured-product");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
