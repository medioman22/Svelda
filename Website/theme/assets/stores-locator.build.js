const selectors = {
  section: ".js-stores-locator",
  tab: ".js-stores-locator-item",
  tabDesktop: ".js-stores-locator-item.js-stores-locator-item-desktop",
  tabMobile: ".js-stores-locator-item.js-stores-locator-item-mobile",
  tabText: ".js-stores-locator-item-text",
  body: ".js-stores-locator-map-wrapper",
  accordionBody: ".js-stores-locator-accordion-body"
};
const StoresLocator = () => {
  const cssClasses = window.themeCore.utils.cssClasses;
  const isMobile = window.matchMedia("(max-width: 991.98px)");
  const classes = {
    tabDesktop: "js-stores-locator-item-desktop",
    tabMobile: "js-stores-locator-item-mobile",
    ...cssClasses
  };
  let isProcessing = false;
  function init(sectionId) {
    const sections = [...document.querySelectorAll(selectors.section)].filter((section) => !sectionId || section.closest(`#shopify-section-${sectionId}`));
    sections.forEach((section) => {
      const tabDesktop = section.querySelector(selectors.tabDesktop);
      const accordionBody = tabDesktop.querySelector(selectors.accordionBody);
      const tabMobile = section.querySelector(selectors.tabMobile);
      accordionBody.style.height = accordionBody.scrollHeight + "px";
      tabMobile.style.height = tabMobile.scrollHeight + "px";
      section.addEventListener("click", handlerTabs);
      isMobile.addEventListener("change", () => {
        const tabs = section.querySelectorAll(selectors.tab);
        tabs.forEach((tab) => {
          hideContent(tab);
        });
      });
      [...section.querySelectorAll(selectors.tab)].forEach((tab) => {
        hideContent(tab);
      });
    });
  }
  function handlerTabs(event) {
    if (isProcessing) {
      return;
    }
    const section = event.target.closest(selectors.section);
    const tab = event.target.closest(selectors.tab);
    if (!section || !tab) {
      return;
    }
    if (tab.classList.contains(classes.active)) {
      return;
    }
    const tabs = [...section.querySelectorAll(selectors.tab)];
    const tabsBody = [...section.querySelectorAll(selectors.body)];
    const index = tab.dataset.index;
    tabsBody.forEach((body) => {
      body.classList.toggle(classes.hidden, body.dataset.index !== index);
    });
    tabs.forEach((tab2) => {
      const isCorrectType = isMobile.matches ? tab2.classList.contains(classes.tabMobile) : tab2.classList.contains(classes.tabDesktop);
      if (isCorrectType) {
        tab2.classList.toggle(classes.active, tab2.dataset.index === index);
      }
      hideContent(tab2);
    });
  }
  function hideContent(element) {
    if (!element) {
      return;
    }
    const accordionBody = element.querySelector(selectors.accordionBody);
    const animationDelay = 500;
    if (isMobile.matches && element.classList.contains(classes.tabMobile)) {
      const elementHeight = element.scrollHeight;
      if (element.classList.contains(classes.active)) {
        isProcessing = true;
        element.style.height = elementHeight + "px";
        element.setAttribute("aria-expanded", true);
        setTimeout(() => {
          element.removeAttribute("style");
          isProcessing = false;
        }, animationDelay);
      } else {
        element.style.height = elementHeight + "px";
        element.setAttribute("aria-expanded", false);
        requestAnimationFrame(() => {
          element.style.height = "86px";
        });
      }
    } else {
      if (accordionBody) {
        const accordionBodyHeight = accordionBody.scrollHeight;
        if (element.classList.contains(classes.active)) {
          isProcessing = true;
          accordionBody.style.height = accordionBodyHeight + "px";
          element.setAttribute("aria-expanded", true);
          setTimeout(() => {
            accordionBody.removeAttribute("style");
            isProcessing = false;
          }, animationDelay);
        } else {
          accordionBody.style.height = accordionBodyHeight + "px";
          element.setAttribute("aria-expanded", false);
          requestAnimationFrame(() => {
            accordionBody.style.height = 0;
          });
        }
      }
    }
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.StoresLocator = window.themeCore.StoresLocator || StoresLocator();
  window.themeCore.utils.register(window.themeCore.StoresLocator, "stores-locator");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
