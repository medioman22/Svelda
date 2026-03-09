import { P as ProductCarousel, a as ProductStickyForm, b as ProductMediaScroller, c as ProductForm } from "./product-sticky-form-e1f0721f.js";
import { d as disableTabulationOnNotActiveSlidesWithModel } from "./disableTabulationOnNotActiveSlidesWithModel-38e80234.js";
const selectors$1 = {
  container: "[data-zoom-container]",
  media: "[data-zoom-media]",
  modal: "[data-zoom-modal]",
  toggle: "[data-zoom-modal-toggle]",
  content: "[data-zoom-content]",
  slider: "[data-zoom-slider]",
  slide: "[data-zoom-slide]",
  modalMedia: ".js-zoom-slider-modal-media",
  prevSlide: ".swiper-button-prev",
  nextSlide: ".swiper-button-next",
  button: "[data-js-zoom-button]",
  productSlider: "[data-js-product-media-slider]",
  productSliderWrapper: ".swiper-wrapper",
  notInitedIframe: ".js-video.js-video-youtube, .js-video:empty"
};
const breakpoints = {
  afterMedium: 1200
};
const Zoom = (context = document) => {
  const Swiper = window.themeCore.utils.Swiper;
  const off = window.themeCore.utils.off;
  const on = window.themeCore.utils.on;
  const Toggle2 = window.themeCore.utils.Toggle;
  const VIDEO_TYPES = window.themeCore.utils.VIDEO_TYPES;
  const Video2 = window.themeCore.utils.Video;
  const globalClasses = window.themeCore.utils.cssClasses;
  let containers = null;
  let isDrag = false;
  async function init2() {
    let zoomSlider = context.querySelector(selectors$1.slider);
    if (!zoomSlider) {
      return;
    }
    let videosSlides = zoomSlider.querySelectorAll(".js-video");
    let hasVideos = videosSlides && videosSlides.length > 0;
    containers = getContainers();
    containers.forEach((container) => {
      if (!container.media.length) {
        return;
      }
      container.modal.init();
      if (hasVideos) {
        initVideos2(container);
      }
      container.slider = initMediaSlider(container);
      const observer = new MutationObserver(() => {
        if (container.el.querySelector(selectors$1.notInitedIframe)) {
          return;
        }
        disableTabulationOnNotActiveSlidesWithModel(container.slider);
        observer.disconnect();
      });
      const observerOptions = {
        attributes: true,
        childList: true,
        subtree: true
      };
      observer.observe(container.el, observerOptions);
      zoomMove(container);
    });
    setEventListeners();
  }
  function zoomMove(container) {
    let pos = { top: 0, left: 0, x: 0, y: 0 };
    const mouseDownHandler = function(e) {
      if (window.innerWidth < breakpoints.afterMedium) {
        return;
      }
      pos = {
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
    };
    const mouseUpHandler = function() {
      off("mousemove", document, mouseMoveHandler);
      off("mouseup", document, mouseUpHandler);
    };
    on("mousedown", container.el, mouseDownHandler);
  }
  function setEventListeners() {
    containers.forEach((container) => {
      on("click", container.el, (e) => onTriggerClick(e, container));
      on("click", container.el, (e) => onSlideClick(e, container));
      on("click", container.el, (e) => onButtonClick(e, container));
      window.themeCore.EventBus.listen(
        `Toggle:${container.modalEl.id}:close`,
        (e) => onZoomModalClose(e, container)
      );
    });
  }
  function getContainers() {
    return [...context.querySelectorAll(selectors$1.container)].map(
      (container) => {
        const media = [...container.querySelectorAll(selectors$1.media)];
        const slides = [...container.querySelectorAll(selectors$1.slide)];
        const content = container.querySelector(selectors$1.content);
        const modalEl = container.querySelector(selectors$1.modal);
        const sliderEl = container.querySelector(selectors$1.slider);
        const button = container.querySelector(selectors$1.button);
        const modal = Toggle2({
          toggleSelector: modalEl.id
        });
        return {
          el: container,
          sliderEl,
          slides,
          modalEl,
          modal,
          media,
          content,
          button
        };
      }
    );
  }
  function initVideos2({ slides }) {
    slides.forEach((slide) => {
      const [video] = Video2({
        videoContainer: slide,
        options: {
          youtube: {
            controls: 1,
            showinfo: 1
          }
        }
      }).init();
      if (video) {
        slide.video = video;
      }
    });
  }
  function initMediaSlider({ sliderEl, slides }) {
    return new Swiper(sliderEl, {
      slidesPerView: 1,
      allowTouchMove: false,
      zoom: {
        maxRatio: 3,
        minRatio: 1
      },
      navigation: {
        prevEl: selectors$1.prevSlide,
        nextEl: selectors$1.nextSlide
      },
      on: {
        beforeSlideChangeStart: function(slider) {
          if (slider && slider.zoom && typeof slider.zoom.out === "function") {
            slider.zoom.out();
          }
        },
        slideChange: function(swiper) {
          pauseAllVideos(slides);
          disableTabulationOnNotActiveSlidesWithModel(swiper);
        }
      }
    });
  }
  function pauseAllVideos(slides) {
    const videoSlides = slides.filter((slide) => slide.video);
    if (!videoSlides.length) {
      return;
    }
    videoSlides.forEach(({ video }) => {
      if (VIDEO_TYPES.youtube === video.type) {
        video.player.pauseVideo();
      } else {
        video.player.pause();
      }
    });
  }
  function onTriggerClick(event, container) {
    const media = event.target.closest(selectors$1.media);
    if (!media || !container.media.length) {
      return;
    }
    removeLoaded(container.modalEl);
    const mediaId = media.dataset.zoomMedia;
    const index = container.slides.findIndex(
      (slide) => slide.dataset.zoomSlide === mediaId
    );
    container.slider.slideTo(index, 0);
    document.querySelector(":root").style.setProperty("--page-height", ` ${window.innerHeight}px`);
    container.modal.open(container.modalEl);
    disableTabulationOnNotActiveSlidesWithModel(container.slider);
    window.themeCore.EventBus.emit("product:zoom:open");
  }
  function onSlideClick(event, container) {
    const slide = event.target.closest(selectors$1.slide);
    if (!slide || isDrag) {
      isDrag = false;
      return;
    }
    container.slider.zoom.toggle();
  }
  function onButtonClick(event, container) {
    const button = event.target.closest(selectors$1.button);
    if (!button) {
      return;
    }
    removeLoaded(container.modalEl);
    const galleryLayout = container.el.dataset.mediaLayout;
    const productSlider = container.el.querySelector(
      selectors$1.productSlider
    );
    if (!productSlider) {
      return;
    }
    let media = null;
    switch (galleryLayout) {
      case "carousel":
        media = productSlider.querySelector(".swiper-slide-active");
        break;
      case "stacked":
        media = [...productSlider.querySelectorAll(".swiper-slide")][0];
        break;
      case "stacked_2_col":
        media = [...productSlider.querySelectorAll(".swiper-slide")][0];
        break;
      default:
        media = [...productSlider.querySelectorAll(".swiper-slide")][0];
        return;
    }
    if (!media || !container.media.length) {
      return;
    }
    const mediaId = media.dataset.zoomMedia || media.dataset.zoomMediaHtmlVideo;
    const index = container.slides.findIndex(
      (slide) => slide.dataset.zoomSlide === mediaId
    );
    container.slider.slideTo(index, 0);
    document.querySelector(":root").style.setProperty("--page-height", ` ${window.innerHeight}px`);
    container.modal.open(container.modalEl);
    disableTabulationOnNotActiveSlidesWithModel(container.slider);
    window.themeCore.EventBus.emit("product:zoom:open");
  }
  function removeLoaded(modal) {
    const modalMedias = modal.querySelectorAll(selectors$1.modalMedia);
    if (modalMedias.length < 1) {
      return;
    }
    modalMedias.forEach((modalMedia) => {
      if (modalMedia.classList.contains(globalClasses.loading)) {
        if (!modalMedia.complete) {
          modalMedia.addEventListener("load", () => {
            modalMedia.classList.remove(globalClasses.loading);
          });
        } else {
          modalMedia.classList.remove(globalClasses.loading);
        }
      }
    });
  }
  function onZoomModalClose(event, container) {
    if (!event) {
      return;
    }
    container.slider.zoom.out();
    pauseAllVideos(container.slides);
  }
  return Object.freeze({
    init: init2
  });
};
const ProductNotifyMe = (section) => {
  const sectionId = section && section.dataset.sectionId;
  const selectors2 = {
    notifyMeButtonContainer: ".js-notify-me-button-container",
    notifyMeButton: ".js-notify-me-button",
    notifyMePopup: ".js-notify-me-popup",
    notifyMeForm: ".js-notify-me-form",
    notifyMeFormStatus: ".js-notify-me-form-status",
    notifyMeFormInputMessage: "[name='contact[message]']",
    notifyMeFormInputProductURL: "[name='contact[ProductURL]']"
  };
  const placeholders = {
    productTitle: "{{ product_title }}"
  };
  const cssClasses = {
    active: "is-active",
    hidden: "is-hidden",
    isPosted: "is-posted",
    isNotifyMeActive: "is-notify-me-popup-active"
  };
  const searchParams = {
    contactPosted: "contact_posted",
    contactProductUrl: "contact[ProductURL]",
    contactMessage: "contact[message]",
    formType: "form_type"
  };
  const Toggle2 = window.themeCore.utils.Toggle;
  const on = window.themeCore.utils.on;
  let notifyMeButtonContainer = null;
  let notifyMeButton = null;
  let notifyMePopup = null;
  let notifyMeForm = null;
  let notifyMeFormInputMessage = null;
  let notifyMeFormInputProductURL = null;
  let notifyMePopupToggle = null;
  let notifyMeFormStatus = null;
  let notifyMeFormId = null;
  let changeVariantIsFired = false;
  function init2() {
    if (!section || !sectionId) {
      return false;
    }
    notifyMeButtonContainer = section.querySelector(selectors2.notifyMeButtonContainer);
    notifyMeButton = section.querySelector(selectors2.notifyMeButton);
    notifyMePopup = section.querySelector(selectors2.notifyMePopup);
    notifyMeForm = section.querySelector(selectors2.notifyMeForm);
    if (!notifyMeButton || !notifyMePopup || !notifyMeForm) {
      return false;
    }
    notifyMeFormId = notifyMeForm.id;
    notifyMeFormInputMessage = notifyMeForm.querySelector(selectors2.notifyMeFormInputMessage);
    notifyMeFormInputProductURL = notifyMeForm.querySelector(selectors2.notifyMeFormInputProductURL);
    notifyMeFormStatus = notifyMeForm.querySelector(selectors2.notifyMeFormStatus);
    if (!notifyMeFormInputMessage || !notifyMeFormInputProductURL || !notifyMeFormStatus) {
      return;
    }
    initToggle();
    initFormStatus();
    setEventBusListeners2();
  }
  function initToggle() {
    notifyMePopupToggle = Toggle2({
      toggleSelector: notifyMePopup.id
    });
    notifyMePopupToggle.init();
    on("click", notifyMePopup, function(e) {
      if (e.target == this) {
        notifyMePopupToggle.close(notifyMePopup);
      }
    });
    window.themeCore.EventBus.listen(`Toggle:${notifyMePopup.id}:close`, closeNotifyMePopup);
    window.themeCore.EventBus.listen(`Toggle:${notifyMePopup.id}:open`, openNotifyMePopup);
  }
  function initFormStatus() {
    if (isCurrentFormPosted()) {
      notifyMeForm.classList.add(cssClasses.isPosted);
      notifyMePopupToggle.open(notifyMePopup);
    }
  }
  function isCurrentFormPosted() {
    return window.location.hash.includes(`#${notifyMeFormId}`) && notifyMeFormStatus.dataset.formStatus === "posted";
  }
  function closeNotifyMePopup() {
    if (isCurrentFormPosted()) {
      setTimeout(() => {
        notifyMeForm.classList.remove(cssClasses.isPosted);
        section.classList.remove(cssClasses.isNotifyMeActive);
      }, 400);
      let newUrl = new URL(window.location.href);
      newUrl.hash = "";
      newUrl.searchParams.delete(searchParams.contactPosted);
      newUrl.searchParams.delete(searchParams.contactProductUrl);
      newUrl.searchParams.delete(searchParams.contactMessage);
      newUrl.searchParams.delete(searchParams.formType);
      window.history.replaceState({}, null, newUrl.toString());
    }
  }
  function openNotifyMePopup() {
    section.classList.add(cssClasses.isNotifyMeActive);
  }
  function setEventBusListeners2() {
    window.themeCore.EventBus.listen(`pdp:section-${sectionId}:change-variant`, onChangeVariant);
    if (!changeVariantIsFired) {
      const productElementJSON = section.querySelector("[data-js-product-json]");
      let productJSON;
      try {
        productJSON = JSON.parse(productElementJSON.innerText);
      } catch {
        productJSON = null;
      }
      if (!productJSON) {
        return;
      }
      if (productJSON.has_only_default_variant) {
        updateFormFields(productJSON.variants[0], productJSON);
        updateNotifyMeButton(productJSON.variants[0]);
      }
    }
  }
  function onChangeVariant({ variant, product }) {
    changeVariantIsFired = true;
    if (!variant || !product) {
      return false;
    }
    updateNotifyMeButton(variant);
    updateFormFields(variant, product);
  }
  function updateFormFields(variant, product) {
    const variantAvailable = variant.available;
    const variantId = variant.id;
    const productURL = product.url;
    const productTitle = product.title;
    if (variantAvailable || !variantId || !productURL || !productTitle) {
      notifyMeFormInputMessage.value = "";
      notifyMeFormInputProductURL.value = "";
      return false;
    }
    const variantURL = `${window.location.origin}${productURL}?variant=${variantId}`;
    const notifyMeMessage = notifyMeFormInputMessage.dataset.notifyMeMessage;
    notifyMeFormInputMessage.value = notifyMeMessage.replace(placeholders.productTitle, productTitle);
    notifyMeFormInputProductURL.value = variantURL;
  }
  function updateNotifyMeButton(variant) {
    const variantAvailable = variant.available;
    if (variantAvailable) {
      notifyMeButtonContainer.classList.add(cssClasses.hidden);
      notifyMeButton.classList.remove(cssClasses.active);
    } else {
      notifyMeButton.classList.add(cssClasses.active);
      notifyMeButtonContainer.classList.remove(cssClasses.hidden);
    }
  }
  return Object.freeze({
    init: init2
  });
};
const ProductAskQuestion = (section) => {
  const sectionId = section && section.dataset.sectionId;
  const selectors2 = {
    askQuestionButton: ".js-ask-question-button",
    askQuestionPopup: ".js-ask-question-popup",
    askQuestionForm: ".js-ask-question-form",
    askQuestionFormStatus: ".js-ask-question-form-status",
    askQuestionFormInputProductURL: "[name='contact[product_url]']"
  };
  const cssClasses = {
    active: "is-active",
    isPosted: "is-posted",
    isNotifyMeActive: "is-ask-question-popup-active"
  };
  const searchParams = {
    contactPosted: "contact_posted",
    contactProductUrl: "contact[product_url]",
    contactMessage: "contact[body]",
    formType: "form_type"
  };
  const Toggle2 = window.themeCore.utils.Toggle;
  const on = window.themeCore.utils.on;
  let askQuestionButton = null;
  let askQuestionPopup = null;
  let askQuestionForm = null;
  let askQuestionFormInputProductURL = null;
  let askQuestionPopupToggle = null;
  let askQuestionFormStatus = null;
  let askQuestionFormId = null;
  let changeVariantIsFired = false;
  function init2() {
    if (!section || !sectionId) {
      return false;
    }
    askQuestionButton = section.querySelector(selectors2.askQuestionButton);
    askQuestionPopup = section.querySelector(selectors2.askQuestionPopup);
    askQuestionForm = section.querySelector(selectors2.askQuestionForm);
    if (!askQuestionButton || !askQuestionPopup || !askQuestionForm) {
      return false;
    }
    askQuestionFormId = askQuestionForm.id;
    askQuestionFormInputProductURL = askQuestionForm.querySelector(selectors2.askQuestionFormInputProductURL);
    askQuestionFormStatus = askQuestionForm.querySelector(selectors2.askQuestionFormStatus);
    if (!askQuestionFormInputProductURL || !askQuestionFormStatus) {
      return;
    }
    initToggle();
    initFormStatus();
    setEventBusListeners2();
  }
  function initToggle() {
    askQuestionPopupToggle = Toggle2({
      toggleSelector: askQuestionPopup.id
    });
    askQuestionPopupToggle.init();
    on("click", askQuestionPopup, function(e) {
      if (e.target == this) {
        askQuestionPopupToggle.close(askQuestionPopup);
      }
    });
    window.themeCore.EventBus.listen(`Toggle:${askQuestionPopup.id}:close`, closeAskQuestionPopup);
    window.themeCore.EventBus.listen(`Toggle:${askQuestionPopup.id}:open`, openQuestionPopup);
  }
  function initFormStatus() {
    if (isCurrentFormPosted()) {
      askQuestionForm.classList.add(cssClasses.isPosted);
      askQuestionPopupToggle.open(askQuestionPopup);
    }
  }
  function isCurrentFormPosted() {
    return window.location.hash.includes(`#${askQuestionFormId}`) && askQuestionFormStatus.dataset.formStatus === "posted";
  }
  function closeAskQuestionPopup() {
    if (isCurrentFormPosted()) {
      setTimeout(() => {
        askQuestionForm.classList.remove(cssClasses.isPosted);
        section.classList.remove(cssClasses.isNotifyMeActive);
      }, 400);
      let newUrl = new URL(window.location.href);
      newUrl.hash = "";
      newUrl.searchParams.delete(searchParams.contactPosted);
      newUrl.searchParams.delete(searchParams.contactProductUrl);
      newUrl.searchParams.delete(searchParams.contactMessage);
      newUrl.searchParams.delete(searchParams.formType);
      window.history.replaceState({}, null, newUrl.toString());
    }
  }
  function openQuestionPopup() {
    section.classList.add(cssClasses.isNotifyMeActive);
  }
  function setEventBusListeners2() {
    window.themeCore.EventBus.listen(`pdp:section-${sectionId}:change-variant`, onChangeVariant);
    if (!changeVariantIsFired) {
      const productElementJSON = section.querySelector("[data-js-product-json]");
      let productJSON;
      try {
        productJSON = JSON.parse(productElementJSON.innerText);
      } catch {
        productJSON = null;
      }
      if (!productJSON) {
        return;
      }
      if (productJSON.has_only_default_variant) {
        updateFormFields(productJSON.variants[0], productJSON);
      }
    }
  }
  function onChangeVariant({ variant, product }) {
    changeVariantIsFired = true;
    if (!variant || !product) {
      return false;
    }
    updateFormFields(variant, product);
  }
  function updateFormFields(variant, product) {
    const variantId = variant.id;
    const productURL = product.url;
    if (!variantId || !productURL) {
      askQuestionFormInputProductURL.value = "";
      return false;
    }
    const variantURL = `${window.location.origin}${productURL}?variant=${variantId}`;
    askQuestionFormInputProductURL.value = variantURL;
  }
  return Object.freeze({
    init: init2
  });
};
const ProductSection = (section) => {
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
    const ProductZoom = Zoom(section);
    Carousel = ProductCarousel({
      selectors: carouselSelectors,
      sectionId
    });
    const productStickyForms = ProductStickyForm(section);
    ProductZoom.init();
    productStickyForms.init();
    initCarousel();
    setDrawers();
    initModelButtons();
    initNotifyMe();
    initAskQuestion();
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
  function initNotifyMe() {
    const productNotifyMe = ProductNotifyMe(section);
    productNotifyMe.init();
  }
  function initAskQuestion() {
    const productAskQuestion = ProductAskQuestion(section);
    productAskQuestion.init();
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
  Video = window.themeCore.utils.Video;
  sections = [...document.querySelectorAll(selectors.section)].filter((section) => !sectionId || section.closest(`#shopify-section-${sectionId}`));
  ProductForms = ProductForm();
  sections.forEach(initSection);
  ProductForms.init();
  initVideos();
  setEventBusListeners();
  window.themeCore.EventBus.emit("product:loaded");
}
function initSection(section) {
  const productSection = ProductSection(section);
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
function onProductSliderSlideChange(event_name) {
  if (!videos.length) {
    window.themeCore.EventBus.remove(event_name, onProductSliderSlideChange);
    return;
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
  window.themeCore.EventBus.listen("product-slider:slide-change", () => onProductSliderSlideChange("product-slider:slide-change"));
  window.themeCore.EventBus.listen("product:zoom:open", () => onProductSliderSlideChange("product:zoom:open"));
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
const Product = () => {
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.Product = window.themeCore.Product || Product();
  window.themeCore.utils.register(window.themeCore.Product, "product-template");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
