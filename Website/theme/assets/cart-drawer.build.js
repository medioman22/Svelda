import { C as Cart } from "./cart-6288397e.js";
const action = () => {
  window.themeCore.Cart = window.themeCore.Cart || Cart();
  window.themeCore.utils.register(window.themeCore.Cart, "cart-drawer");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
