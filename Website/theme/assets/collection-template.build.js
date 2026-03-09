const CollectionTemplate = () => {
  const selectors = {
    section: ".js-collection",
    swiper: ".js-collection-list-swiper",
    swiperNextBtn: ".js-collection-list-button-next",
    swiperPrevBtn: ".js-collection-list-button-prev",
    gridViewButton: ".js-grid-view-btn",
    gridViewButtons: ".js-grid-view-buttons",
    grid: ".js-grid-wrapper",
    getActiveButton: (customerGridView) => `.js-grid-view-btn[data-grid-cols="${customerGridView}"]`,
    defaultButton: ".js-grid-view-btn[data-grid-cols='4']"
  };
  const localStorageKeys = {
    collectionGridCols: "collection-grid-cols"
  };
  const attributes = {
    gridCol: "data-grid-col",
    gridColButton: "data-grid-cols"
  };
  const Swiper = window.themeCore.utils.Swiper;
  const cssClasses = {
    hiddenCollectionOnLoad: "collection__grid-wrapper-hide-on-load",
    ...window.themeCore.utils.cssClasses
  };
  async function init() {
    const ProductFilters = await window.themeCore.utils.getExternalUtil("ProductFilters");
    const section = document.querySelector(selectors.section);
    const gridViewButtons = document.querySelectorAll(selectors.gridViewButton);
    const swiper = document.querySelector(selectors.swiper);
    initSlider(swiper);
    ProductFilters(section).init();
    if (gridViewButtons.length > 0) {
      initGridViewButtons(gridViewButtons);
    }
  }
  function initGridViewButtons(gridButtons) {
    const productsGrid = document.querySelector(selectors.grid);
    const customerGridView = localStorage.getItem(localStorageKeys.collectionGridCols);
    const gridViewButtonsWrapper = document.querySelector(selectors.gridViewButtons);
    const defaultButton = document.querySelector(selectors.defaultButton);
    if (customerGridView) {
      const activeButton = document.querySelector(selectors.getActiveButton(customerGridView));
      productsGrid.setAttribute(attributes.gridCol, customerGridView);
      defaultButton.classList.remove(cssClasses.active);
      activeButton.classList.add(cssClasses.active);
    }
    productsGrid.classList.remove(cssClasses.hiddenCollectionOnLoad);
    gridViewButtonsWrapper.classList.add("animated");
    gridButtons.forEach(function(button) {
      button.addEventListener("click", function() {
        const gridView = button.getAttribute(attributes.gridColButton);
        if (button.classList.contains(cssClasses.active)) {
          return;
        }
        const currentActive = [...gridButtons].find((el) => el.classList.contains(cssClasses.active));
        const newActive = button;
        currentActive.classList.remove(cssClasses.active);
        newActive.classList.add(cssClasses.active);
        productsGrid.setAttribute(attributes.gridCol, gridView);
        if (gridView === "3" || gridView === "2") {
          localStorage.setItem(localStorageKeys.collectionGridCols, gridView);
        } else {
          localStorage.removeItem(localStorageKeys.collectionGridCols);
        }
      });
    });
  }
  function initSlider(slider) {
    if (!slider)
      return;
    new Swiper(slider, {
      slidesPerView: 2.7,
      navigation: {
        nextEl: selectors.swiperNextBtn,
        prevEl: selectors.swiperPrevBtn
      },
      breakpoints: {
        576: {
          slidesPerView: 4.7
        },
        992: {
          slidesPerView: 6,
          spaceBetween: 16
        },
        1200: {
          slidesPerView: 8,
          spaceBetween: 16
        },
        1500: {
          slidesPerView: 10,
          spaceBetween: 16
        }
      }
    });
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.CollectionTemplate = window.themeCore.CollectionTemplate || CollectionTemplate();
  window.themeCore.utils.register(window.themeCore.CollectionTemplate, "collection-template");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
