const MyFavorites = () => {
  const selectors = {
    favoritesButton: ".js-favorites-product-button",
    clearAllButton: ".js-favorites-clear-all",
    favoritesContainer: ".js-favorites-container",
    favoritesHeaderIcon: ".js-favorites-header-icon",
    productCard: ".js-product-card",
    emptyMessage: ".js-favorites-empty-text",
    pageLoader: ".js-page-preloader"
  };
  const attributes = {
    productHandle: "data-product-handle",
    productTitle: "data-product-title",
    ariaLabel: "aria-label",
    count: "data-count",
    empty: "data-empty"
  };
  const MAX_FAVORITES_PRODUCTS = 12;
  const classes = {
    ...window.themeCore.utils.cssClasses
  };
  let isMyFavoritesPage = !!document.querySelector(selectors.favoritesContainer);
  let favoritesHeaderIcon, translations, emptyMessage;
  const pageLoader = document.querySelector(selectors.pageLoader);
  function init() {
    favoritesHeaderIcon = document.querySelectorAll(selectors.favoritesHeaderIcon);
    if (!favoritesHeaderIcon.length) {
      return;
    }
    initFavoritesButtons();
    setInitLister();
    addEventListeners();
    if (isMyFavoritesPage) {
      initMyFavoritesPage();
    }
  }
  function setInitLister() {
    window.themeCore.EventBus.listen(`favorites-list:init`, initFavoritesButtons);
  }
  function initFavoritesButtons() {
    const favoritesButtons = document.querySelectorAll(selectors.favoritesButton);
    const favoritesProducts = getFavoritesProducts();
    if (isMyFavoritesPage) {
      favoritesHeaderIcon.forEach(function(icon) {
        icon.setAttribute(attributes.count, favoritesProducts.length);
      });
      if (favoritesProducts.length > 0) {
        favoritesHeaderIcon.forEach(function(icon) {
          icon.classList.add(classes.active);
        });
        if (emptyMessage) {
          emptyMessage.classList.add(classes.hidden);
        }
      } else {
        favoritesHeaderIcon.forEach(function(icon) {
          icon.classList.remove(classes.active);
        });
        if (emptyMessage) {
          emptyMessage.classList.remove(classes.hidden);
        }
      }
    }
    favoritesHeaderIcon.forEach(function(icon) {
      icon.setAttribute(attributes.count, favoritesProducts.length);
      icon.classList.toggle(classes.active, favoritesProducts.length > 0);
    });
    if (!favoritesButtons.length) {
      return;
    }
    translations = {
      add: window.themeCore.translations.get("products.favorites.add_to_favorites"),
      remove: window.themeCore.translations.get("products.favorites.remove_from_favorites"),
      error: window.themeCore.translations.get("products.favorites.quantity_error")
    };
    favoritesButtons.forEach((button) => {
      const productHandle = button.getAttribute(attributes.productHandle);
      if (!productHandle) {
        return;
      }
      const productTitle = button.getAttribute(attributes.productTitle);
      if (productTitle) {
        const translationKey = favoritesProducts.includes(productHandle) ? "remove" : "add";
        const ariaLabel = translations[translationKey].replaceAll("{{ product }}", productTitle);
        button.setAttribute(attributes.ariaLabel, ariaLabel);
      }
      button.classList.toggle(classes.active, favoritesProducts.includes(productHandle));
      button.classList.remove(classes.hidden);
    });
  }
  function getFavoritesProducts() {
    const products = localStorage.getItem("theme-favorites-list");
    if (!products) {
      return [];
    }
    try {
      return JSON.parse(products);
    } catch (e) {
      return [];
    }
  }
  function addEventListeners() {
    document.addEventListener("click", addToMyFavoritesClickHandler);
  }
  function addToMyFavoritesClickHandler(event) {
    const favoritesButton = event.target.closest(selectors.favoritesButton);
    if (!favoritesButton) {
      return;
    }
    const productHandle = favoritesButton.getAttribute(attributes.productHandle);
    if (!productHandle) {
      return;
    }
    toggleProduct(productHandle);
  }
  function toggleProduct(productHandle) {
    let products = getFavoritesProducts();
    if (products.includes(productHandle)) {
      products = products.filter((productElement) => productElement !== productHandle);
      if (isMyFavoritesPage) {
        removeProductCard(productHandle);
      }
    } else {
      products = [...products, productHandle];
    }
    setFavoritesProducts(products);
  }
  function removeProduct(productHandle) {
    let products = getFavoritesProducts();
    products = products.filter((productElement) => productElement !== productHandle);
    setFavoritesProducts(products);
  }
  function setFavoritesProducts(products) {
    if (!products) {
      return;
    }
    if (products.length > MAX_FAVORITES_PRODUCTS) {
      showErrorNotification();
      return;
    }
    localStorage.setItem("theme-favorites-list", JSON.stringify(products));
    initFavoritesButtons();
  }
  function showErrorNotification() {
    setTimeout(() => {
      const CartNotificationError = window.themeCore.CartNotificationError;
      CartNotificationError.addNotification(translations.error, window.themeCore.translations.get("products.favorites.quantity_error_heading"));
      CartNotificationError.open();
    });
  }
  function removeProductCard(productHandle) {
    if (!productHandle) {
      return;
    }
    const favoritesContainer = document.querySelector(selectors.favoritesContainer);
    if (!favoritesContainer) {
      return;
    }
    const favoritesButton = favoritesContainer.querySelector(`${selectors.favoritesButton}[${attributes.productHandle}="${productHandle}"]`);
    if (!favoritesButton) {
      return;
    }
    const productCard = favoritesButton.closest(".js-favorites-item");
    if (productCard) {
      productCard.remove();
    }
  }
  async function initMyFavoritesPage() {
    let products = getFavoritesProducts();
    let productsList = await getProductCards();
    productsList.forEach((card, index) => !card && removeProduct(products[index]));
    productsList = productsList.filter(Boolean);
    insertFavoritesCards(productsList);
    emptyMessage = document.querySelector(selectors.emptyMessage);
    if (productsList.length === 0 && emptyMessage) {
      emptyMessage.classList.remove(classes.hidden);
    }
    window.themeCore.LazyLoadImages.init();
    initFavoritesButtons();
    window.themeCore.EventBus.emit("compare-products:init");
    setTimeout(() => {
      pageLoader.classList.remove(classes.active);
    }, 300);
  }
  async function getProductCards() {
    const products = getFavoritesProducts();
    try {
      return await Promise.all(products.map((productHandle) => getProductCard(productHandle)));
    } catch (error) {
      console.log(error);
    }
  }
  async function getProductCard(productHandle) {
    const url = `/products/${productHandle}?view=card`;
    return await getHTML(url, selectors.productCard);
  }
  async function getHTML(url, selector) {
    try {
      const response = await fetch(url);
      const resText = await response.text();
      let result = new DOMParser().parseFromString(resText, "text/html");
      if (selector) {
        result = result.querySelector(selector);
      }
      return result;
    } catch (error) {
      console.log("error:", error);
    }
  }
  function insertFavoritesCards(nodesArray) {
    if (!nodesArray.length) {
      return;
    }
    const favoritesGrid = document.querySelector(selectors.favoritesContainer);
    if (!favoritesGrid) {
      return;
    }
    nodesArray.forEach((nodeEl) => {
      let favoritesCardItem = document.createElement("div");
      favoritesCardItem.classList.add("favorites-grid__item", "js-favorites-item");
      favoritesCardItem.append(nodeEl);
      favoritesGrid.append(favoritesCardItem);
    });
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.MyFavorites = window.themeCore.MyFavorites || MyFavorites();
  window.themeCore.utils.register(window.themeCore.MyFavorites, "my-favorites");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action);
}
