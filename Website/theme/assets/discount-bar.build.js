const selectors = {
  buttonWrapper: ".js-discount-bar-button-wrapper",
  button: ".js-discount-bar-copy-button"
};
const classes = {
  copied: "discount-bar__button-wrapper--copied"
};
const DiscountBar = () => {
  function init() {
    const buttonWrapper = document.querySelector(selectors.buttonWrapper);
    const button = document.querySelector(selectors.button);
    if (!button || !buttonWrapper) {
      return;
    }
    button.addEventListener("click", () => {
      navigator.clipboard.writeText(button.dataset.discountCode);
      buttonWrapper.classList.add(classes.copied);
    });
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.DiscountBar = window.themeCore.DiscountBar || DiscountBar();
  window.themeCore.utils.register(window.themeCore.DiscountBar, "discount-bar");
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
