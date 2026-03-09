const selectors = {
  announcementBar: ".js-announcement-bar",
  header: ".header-section",
  headerInner: ".js-header",
  headerDrawerToggler: ".js-header-drawer-toggler",
  headerDrawerCloseButton: ".js-header-drawer-close-button",
  drawerMenu: "#headerDrawerMenu",
  mainMenuToggler: ".js-main-menu-toggler",
  headerMenu: ".js-mobile-header-menu",
  headerMainMenu: ".js-mobile-header-main-menu",
  headerMenuToggler: ".js-mobile-header-menu-toggler",
  headerDropdownToggler: ".js-header-dropdown-menu-toggler",
  headerDropdownMenu: ".js-header-dropdown-menu",
  headerMegaMenu: ".js-header-mega-menu",
  headerMegaMenuToggler: ".js-header-mega-menu-toggler",
  headerMegaMenuTogglerNested: ".js-header-mega-menu-toggler-nested",
  headerMegaMenuNested: ".js-header-mega-menu-nested",
  headerCartItemCount: ".js-header-cart-item-count",
  headerCartItemCountWrapper: ".js-header-cart-item-count-wrapper",
  predictiveSearchInput: ".js-predictive-search-input",
  headerContent: "[data-open-menu-type]",
  headerDropdownMenuElement: ".js-header-dropdown-menu-element",
  headerMegaMenuContent: ".js-header-mega-menu-content",
  localizationForm: ".js-localization-form",
  localizationInput: "input[name='language_code'], input[name='country_code']",
  localizationButton: ".js-disclosure__button",
  localizationPanel: ".js-disclosure-list",
  localizationLink: ".js-disclosure__link"
};
const attributes = {
  drawerToggle: "data-js-toggle",
  itemCount: "data-cart-count",
  hideOnScrollDown: "data-hide-on-scroll-down",
  headerTransparent: "data-header-transparent",
  staticHeader: "data-static-header",
  ariaExpanded: "aria-expanded",
  hidden: "hidden",
  tabIndex: "tabindex"
};
const cssVariables = {
  headerHeight: "--header-height",
  headerHeightStatic: "--header-height-static",
  headerOffsetTop: "--header-offset-top",
  headerOffsetTopStatic: "--header-offset-top-static",
  pageHeight: "--page-height",
  announcementBarHeight: "--announcement-bar-height"
};
const Header = () => {
  const Toggle = window.themeCore.utils.Toggle;
  const cssClasses = window.themeCore.utils.cssClasses;
  const isElement = window.themeCore.utils.isElement;
  const on = window.themeCore.utils.on;
  const focusable = window.themeCore.utils.focusable;
  const removeTrapFocus = window.themeCore.utils.removeTrapFocus;
  const trapFocus = window.themeCore.utils.trapFocus;
  const bind = window.themeCore.utils.bind;
  const debounce = window.themeCore.utils.debounce;
  const binder = bind(document.documentElement, {
    className: "esc-bind"
  });
  let cssRoot, announcementBar, header, headerInner, headerCartItemCount, headerContent, openMenuType, headerMegaMenuTogglersOpenEvent, headerCartItemCountWrapper, headerDrawerTogglers, drawerMenu, mainMenuToggler, headerDrawerCloseButton, headerMenuTogglers, headerDropdownTogglers, headerDropdownMenus, headerMegaMenuTogglers, headerMegaMenus, headerMegaMenuTogglersNested, headerMegaMenusNested, previouslySelectedElement, headerMenuList, headerMainMenu, headerHeight, headerHeightStatic, hideOnScrollDown, headerTransparent, staticHeader, lastScrollPosition, isHeaderHidden, openProcessing;
  const mediaQuery = "(min-width: 1200px)";
  const mediaQueryList = window.matchMedia(mediaQuery);
  function init() {
    cssRoot = document.querySelector(":root");
    header = document.querySelector(selectors.header);
    headerInner = document.querySelector(selectors.headerInner);
    announcementBar = document.querySelector(selectors.announcementBar);
    if (!header) {
      return;
    }
    lastScrollPosition = document.documentElement.scrollTop || document.body.scrollTop;
    headerCartItemCount = header.querySelector(selectors.headerCartItemCount);
    headerContent = header.querySelector(selectors.headerContent);
    hideOnScrollDown = headerContent.hasAttribute(attributes.hideOnScrollDown);
    headerTransparent = headerContent.hasAttribute(attributes.headerTransparent);
    staticHeader = headerContent.hasAttribute(attributes.staticHeader);
    openMenuType = headerContent.dataset.openMenuType;
    headerMegaMenuTogglersOpenEvent = openMenuType === "click" ? "click" : "mouseenter";
    headerCartItemCountWrapper = header.querySelector(selectors.headerCartItemCountWrapper);
    if (headerTransparent) {
      header.classList.add("header-section--transparent", "header-section--top-position");
    }
    headerDrawerTogglers = [...header.querySelectorAll(selectors.headerDrawerToggler)];
    drawerMenu = header.querySelector(selectors.drawerMenu);
    mainMenuToggler = header.querySelector(selectors.mainMenuToggler);
    headerDrawerCloseButton = header.querySelector(selectors.headerDrawerCloseButton);
    headerMainMenu = header.querySelector(selectors.headerMainMenu);
    headerMenuTogglers = [...header.querySelectorAll(selectors.headerMenuToggler)];
    headerMenuList = [];
    if (drawerMenu) {
      headerMenuList = [...drawerMenu.querySelectorAll(selectors.headerMenu)];
    }
    headerDropdownTogglers = [...header.querySelectorAll(selectors.headerDropdownToggler)];
    headerDropdownMenus = [...header.querySelectorAll(selectors.headerDropdownMenu)];
    headerMegaMenuTogglers = [...header.querySelectorAll(selectors.headerMegaMenuToggler)];
    headerMegaMenus = [...header.querySelectorAll(selectors.headerMegaMenu)];
    headerMegaMenuTogglersNested = [...header.querySelectorAll(selectors.headerMegaMenuTogglerNested)];
    headerMegaMenusNested = [...header.querySelectorAll(selectors.headerMegaMenuNested)];
    previouslySelectedElement = {};
    headerHeight = getHeaderHeight();
    headerHeightStatic = headerHeight;
    openProcessing = false;
    initDrawers();
    setEventListeners();
    setEventBusListeners();
    setHeaderVariables();
    headerTopPositionHandler();
  }
  function setEventListeners() {
    on(
      "scroll",
      debounce(() => setTimeout(updateHeaderVariables, 0), 10, false)
    );
    on("resize", () => updateHeaderVariables());
    if (headerTransparent) {
      on(
        "scroll",
        debounce(() => setTimeout(headerTopPositionHandler, 0), 0, false)
      );
      on("resize", () => headerTopPositionHandler());
      on("mouseover", header, () => {
        if (!header.classList.contains(cssClasses.hover)) {
          header.classList.add(cssClasses.hover);
        }
        updateHeaderVariables();
      });
      on("focusin", header, () => {
        if (!header.classList.contains(cssClasses.hover)) {
          header.classList.add(cssClasses.hover);
        }
        updateHeaderVariables();
      });
      on("mouseleave", header, () => {
        if (header.classList.contains(cssClasses.hover)) {
          if (!getActiveElements(headerMegaMenus).length && !getActiveElements(headerDropdownMenus).length && !getActiveElements(headerMegaMenusNested).length && !hasActiveLocalizationPanel()) {
            header.classList.remove(cssClasses.hover);
          }
        }
        updateHeaderVariables();
      });
      on("focusout", header, (e) => {
        if (!headerInner.contains(e.relatedTarget)) {
          if (header.classList.contains(cssClasses.hover)) {
            if (!getActiveElements(headerMegaMenus).length && !getActiveElements(headerDropdownMenus).length && !getActiveElements(headerMegaMenusNested).length && !hasActiveLocalizationPanel()) {
              header.classList.remove(cssClasses.hover);
            }
          }
          updateHeaderVariables();
        }
      });
    }
    if (headerDrawerCloseButton) {
      on("click", headerDrawerCloseButton, () => window.themeCore.EventBus.emit("Toggle:headerToggleMenuDrawer:close"));
    }
    if (drawerMenu) {
      on("change", mediaQueryList, (event) => {
        if (event.matches) {
          if (isTargetActive(drawerMenu)) {
            window.themeCore.EventBus.emit("Toggle:headerToggleMenuDrawer:close");
          }
        } else {
          if (getActiveElements(headerDropdownMenus).length) {
            closeAllMenus(getActiveElements(headerDropdownMenus));
          }
          if (getActiveElements(headerMegaMenus).length) {
            closeAllMenus(getActiveElements(headerMegaMenus));
          }
          if (getActiveElements(headerMegaMenusNested)) {
            closeAllMenus(getActiveElements(headerMegaMenusNested));
          }
        }
      });
    }
    if (headerDropdownTogglers) {
      headerDropdownTogglers.forEach((toggler) => {
        const target = document.getElementById(toggler.dataset.target);
        on(headerMegaMenuTogglersOpenEvent, toggler, (event) => {
          closeAllMenus(headerDropdownMenus.filter((menu) => menu !== target));
          closeAllMenus(headerMegaMenus.filter((menu) => menu !== target));
          openMenuType === "hover" ? openToggleTarget(target, false) : handleToggleEvent(event, target, false, toggler);
        });
        openMenuType === "hover" && on("click", toggler, (event) => {
          if (toggler.matches(":not(:focus-visible)")) {
            return;
          }
          closeAllMenus(headerDropdownMenus.filter((menu) => menu !== target));
          handleToggleEvent(event, target, false, toggler);
        });
      });
      on("click", document, (event) => {
        if (!event.target.closest(selectors.headerDropdownMenu) && getActiveElements(headerDropdownMenus).length) {
          if (openMenuType === "hover" && event.target.matches(":not(:focus-visible)")) {
            return;
          }
          closeAllMenus(getActiveElements(headerDropdownMenus));
          window.themeCore.Accordion.collapseAllItems(selectors.headerDropdownMenu);
        }
      });
    }
    if (headerMenuTogglers) {
      headerMenuTogglers.forEach((toggler) => {
        const target = document.getElementById(toggler.dataset.target);
        on("click", toggler, (event) => {
          if (openProcessing) {
            return;
          }
          let isNested = false;
          let targetMenu = document.getElementById(event.target.closest(selectors.headerMenuToggler).dataset.target);
          if (isTargetActive(targetMenu)) {
            isNested = true;
          }
          handleToggleEvent(event, target, true, 700, true, false);
          if (isNested) {
            let nextTarget;
            if (targetMenu.dataset.menuType === "deep-nested") {
              if (targetMenu.closest('[data-menu-type="deep-nested"]')) {
                drawerMenu.classList.remove(cssClasses.grandChildActive);
                nextTarget = targetMenu.closest('[data-menu-type="nested"]');
              }
            } else if (targetMenu.dataset.menuType === "nested") {
              if (targetMenu.closest('[data-menu-type="nested"]')) {
                drawerMenu.classList.remove(cssClasses.childActive);
                nextTarget = targetMenu.closest('[data-menu-type="main"]');
              }
            }
            if (nextTarget) {
              focusTarget(nextTarget);
            }
            if (!binder.isSet()) {
              binder.set();
            }
          } else {
            if (targetMenu.dataset.menuType === "deep-nested") {
              if (targetMenu.closest('[data-menu-type="deep-nested"]')) {
                drawerMenu.classList.add(cssClasses.grandChildActive);
              }
            } else if (targetMenu.dataset.menuType === "nested") {
              if (targetMenu.closest('[data-menu-type="nested"]')) {
                drawerMenu.classList.add(cssClasses.childActive);
                headerMainMenu.scrollTop = 0;
              }
            }
            setTabIndexOnTarget(targetMenu);
          }
        });
      });
    }
    if (headerMegaMenuTogglers) {
      headerMegaMenuTogglers.forEach((toggler) => {
        const target = document.getElementById(toggler.dataset.target);
        const togglerWrapper = toggler.closest(selectors.headerDropdownMenuElement);
        const currentHeaderMegaMenusNested = togglerWrapper.querySelector(selectors.headerMegaMenuNested);
        const nested = togglerWrapper.querySelector(selectors.headerMegaMenuTogglerNested);
        const isCurrentHeaderMegaMenusNested = nested && nested.closest(".header-mega-menu__menu-item-wrapper").matches(":first-child");
        const headerMegaMenuTogglersOpenHandler = (event, isClickInitiator) => {
          if (openProcessing) {
            return;
          }
          closeAllMenus(headerMegaMenus.filter((menu) => menu !== target));
          closeAllMenus(headerDropdownMenus.filter((menu) => menu !== target));
          if (getActiveElements(headerMegaMenusNested).length) {
            closeAllMenus(headerMegaMenusNested, true, 0);
          }
          let isMobile = window.matchMedia("(hover: none)").matches;
          if (isClickInitiator) {
            handleToggleEvent(event, target, isMobile, 500);
          } else {
            openMenuType === "hover" ? openToggleTarget(target, isMobile) : handleToggleEvent(event, target, isMobile);
          }
          setTimeout(() => {
            isCurrentHeaderMegaMenusNested && isTargetActive(target) && openToggleTarget(currentHeaderMegaMenusNested, false, false);
          });
        };
        openMenuType === "hover" && on(headerMegaMenuTogglersOpenEvent, toggler, headerMegaMenuTogglersOpenHandler);
        on("click", toggler, (event) => {
          if (openMenuType === "hover" && toggler.matches(":not(:focus-visible)")) {
            return;
          }
          headerMegaMenuTogglersOpenHandler(event, true);
        });
      });
    }
    if (headerMegaMenuTogglersNested) {
      headerMegaMenuTogglersNested.forEach((toggler) => {
        const target = document.getElementById(toggler.dataset.target);
        on("click", toggler, (event) => {
          let targetMenu = document.getElementById(event.target.closest(selectors.headerMegaMenuTogglerNested).dataset.target);
          if (!isTargetActive(targetMenu)) {
            closeAllMenus(
              headerMegaMenusNested.filter((menu) => menu !== target),
              false,
              0
            );
            let isMobile = window.matchMedia("(hover: none)").matches;
            openToggleTarget(target, isMobile, false);
            setTimeout(() => focusable(targetMenu)[0].focus(), 0);
          }
        });
      });
    }
    if (openMenuType === "hover") {
      headerMegaMenuTogglers.forEach((toggler) => {
        const togglerWrapper = toggler.closest(selectors.headerDropdownMenuElement);
        const megaMenu = togglerWrapper.querySelector(selectors.headerMegaMenu);
        const megaMenuContent = togglerWrapper.querySelector(selectors.headerMegaMenuContent);
        const needToRemoveMegaMenu = () => {
          return toggler.matches(":not(:hover)") && megaMenuContent.matches(":not(:hover)") && isTargetActive(megaMenu);
        };
        const mouseleaveHandler = () => {
          let timeout = 1e3;
          if (headerTransparent) {
            timeout = 500;
          }
          setTimeout(() => {
            needToRemoveMegaMenu() && !closeAllMenus(headerMegaMenus) && getActiveElements(headerMegaMenusNested).length && closeAllMenus(headerMegaMenusNested);
          }, timeout);
        };
        on("mouseleave", togglerWrapper, mouseleaveHandler);
        on("mouseleave", megaMenuContent, mouseleaveHandler);
      });
      headerDropdownTogglers.forEach((toggler) => {
        const needToRemoveDropdown = () => {
          return toggler.matches(":not(:hover)") && target.matches(":not(:hover)") && isTargetActive(target);
        };
        const target = document.getElementById(toggler.dataset.target);
        const mouseleaveHandler = () => {
          let timeout = 500;
          if (headerTransparent) {
            timeout = 200;
          }
          setTimeout(() => {
            needToRemoveDropdown() && closeAllMenus(headerDropdownMenus);
          }, timeout);
        };
        on("mouseleave", toggler, mouseleaveHandler);
        on("mouseleave", target, mouseleaveHandler);
      });
    }
    on("click", document, (event) => {
      if (!event.target.closest(selectors.headerMegaMenu) && getActiveElements(headerMegaMenus).length) {
        if (openMenuType === "hover" && event.target.matches(":not(:focus-visible)")) {
          return;
        }
        closeAllMenus(getActiveElements(headerMegaMenus));
        if (getActiveElements(headerMegaMenusNested).length) {
          closeAllMenus(getActiveElements(headerMegaMenusNested));
        }
      }
      if (!event.target.closest(selectors.headerDropdownMenu) && getActiveElements(headerDropdownMenus).length) {
        if (openMenuType === "hover" && event.target.matches(":not(:focus-visible)")) {
          return;
        }
        closeAllMenus(getActiveElements(headerDropdownMenus));
        window.themeCore.Accordion.collapseAllItems(selectors.headerDropdownMenu);
      }
      if (hasActiveLocalizationPanel()) {
        closeLocalizationSelector();
      }
    });
    if (hideOnScrollDown || staticHeader) {
      document.addEventListener("scroll", scrollHandler);
    }
  }
  function setEventBusListeners() {
    window.themeCore.EventBus.listen(["EscEvent:on", "Overlay:headerToggleMenuDrawer:close", "Toggle:headerToggleMenuDrawer:close"], () => {
      removeActiveClass(mainMenuToggler);
      if (getActiveElements(headerMenuList).length) {
        closeAllMenus(getActiveElements(headerMenuList));
      }
      if (getActiveElements(headerDropdownMenus).length) {
        closeAllMenus(getActiveElements(headerDropdownMenus));
        window.themeCore.Accordion.collapseAllItems(selectors.headerDropdownMenu);
      }
      if (getActiveElements(headerMegaMenus).length) {
        closeAllMenus(getActiveElements(headerMegaMenus));
      }
      if (getActiveElements(headerMegaMenusNested).length) {
        closeAllMenus(getActiveElements(headerMegaMenusNested));
      }
      drawerMenu.classList.remove(cssClasses.childActive);
      drawerMenu.classList.remove(cssClasses.grandChildActive);
    });
    window.themeCore.EventBus.listen("Toggle:headerToggleMenuDrawer:open", () => {
      addActiveClass(mainMenuToggler);
    });
    window.themeCore.EventBus.listen("cart:updated", (e) => {
      updateItemCount(e);
    });
    window.themeCore.EventBus.listen("Header:loaded", () => {
      headerDropdownMenus.forEach((menu) => {
        addHiddenClass(menu);
      });
    });
    window.themeCore.EventBus.listen(["announcement-bar:loaded", "announcement-bar:changed"], () => {
      updateHeaderVariables();
      headerTopPositionHandler();
    });
    window.themeCore.EventBus.listen("Toggle:headerBoxShadow", (e) => {
      toggleBoxShadow(e);
    });
  }
  function setHeaderVariables() {
    changeCssVariable(cssVariables.headerHeight, ` ${getHeaderHeight()}px`);
    changeCssVariable(cssVariables.headerHeightStatic, ` ${getHeaderHeight()}px`);
    changeCssVariable(cssVariables.headerOffsetTop, ` ${getHeaderOffsetTop()}px`);
    changeCssVariable(cssVariables.headerOffsetTopStatic, ` ${getHeaderOffsetTop()}px`);
    changeCssVariable(cssVariables.pageHeight, ` ${window.innerHeight}px`);
    changeCssVariable(cssVariables.announcementBarHeight, ` ${getAnnouncementBarHeight()}px`);
  }
  function updateHeaderVariables() {
    if (isHeaderHidden) {
      changeCssVariable(cssVariables.headerHeight, `0px`);
      headerHeight = 0;
      changeCssVariable(cssVariables.headerOffsetTop, `0px`);
      changeCssVariable(cssVariables.pageHeight, ` ${window.innerHeight}px`);
      return;
    }
    if (getHeaderHeight() !== headerHeight) {
      changeCssVariable(cssVariables.headerHeight, ` ${getHeaderHeight()}px`);
      changeCssVariable(cssVariables.headerHeightStatic, ` ${getHeaderHeight()}px`);
      headerHeight = getHeaderHeight();
      headerHeightStatic = headerHeight;
    }
    if (getHeaderOffsetTop() > 0) {
      changeCssVariable(cssVariables.headerOffsetTop, ` ${Math.max(getHeaderOffsetTop(), 0)}px`);
      if (getHeaderOffsetTop() > parseInt(getCssVariable(cssVariables.headerOffsetTopStatic))) {
        changeCssVariable(cssVariables.headerOffsetTopStatic, ` ${Math.max(getHeaderOffsetTop(), 0)}px`);
      }
    } else if (getCssVariable(cssVariables.headerOffsetTop) !== " 0px") {
      changeCssVariable(cssVariables.headerOffsetTop, ` ${Math.max(getHeaderOffsetTop(), 0)}px`);
    }
    changeCssVariable(cssVariables.pageHeight, ` ${window.innerHeight}px`);
    changeCssVariable(cssVariables.announcementBarHeight, ` ${getAnnouncementBarHeight()}px`);
  }
  function updateItemCount(event) {
    if (!event.hasOwnProperty("item_count")) {
      return;
    }
    headerCartItemCountWrapper.setAttribute(attributes.itemCount, event.item_count);
    headerCartItemCount.innerHTML = event.item_count;
    if (event.item_count > 99) {
      headerCartItemCount.innerHTML = "99+";
    } else {
      headerCartItemCount.innerHTML = event.item_count;
    }
  }
  function changeCssVariable(variable, value) {
    cssRoot.style.setProperty(variable, value);
  }
  function getCssVariable(variable) {
    return cssRoot.style.getPropertyValue(variable);
  }
  function getHeaderHeight() {
    return header.getBoundingClientRect().height;
  }
  function getAnnouncementBarHeight() {
    if (window.Shopify.designMode) {
      announcementBar = document.querySelector(selectors.announcementBar);
    }
    if (!announcementBar) {
      return 0;
    }
    return announcementBar.getBoundingClientRect().height;
  }
  function getHeaderOffsetTop() {
    let headerPosition = headerInner.hasAttribute("data-static-header") ? 0 : header.getBoundingClientRect().top;
    return headerPosition;
  }
  function initDrawers() {
    headerDrawerTogglers.forEach((drawerToggler) => {
      let toggle = drawerToggler.getAttribute(attributes.drawerToggle);
      if (toggle === "searchToggleDrawer") {
        const input = document.querySelector(selectors.predictiveSearchInput);
        Toggle({
          toggleSelector: toggle,
          toggleTabIndex: true,
          elementToFocus: input
        }).init();
        return;
      }
      Toggle({
        toggleSelector: toggle,
        toggleTabIndex: true,
        overlayPlacement: header
      }).init();
    });
  }
  function isTargetActive(target) {
    return target.classList.contains(cssClasses.active);
  }
  function handleToggleEvent(event, target, bodyScroll, timeout, isTrapFocus, isRemoveTrapFocus) {
    event.preventDefault();
    if (timeout === void 0) {
      timeout = 200;
    }
    openProcessing = true;
    if (isTrapFocus === void 0) {
      isTrapFocus = true;
    }
    if (isRemoveTrapFocus === void 0) {
      isRemoveTrapFocus = true;
    }
    toggleActive(target, bodyScroll, timeout, isTrapFocus, isRemoveTrapFocus);
    setTimeout(() => openProcessing = false, timeout);
  }
  function toggleActive(target, bodyScroll, timeout, isTrapFocus, isRemoveTrapFocus) {
    return isTargetActive(target) ? closeToggleTarget(target, !bodyScroll, timeout, isRemoveTrapFocus) : openToggleTarget(target, bodyScroll, isTrapFocus);
  }
  function openToggleTarget(target, bodyScroll, isTrapFocus) {
    const scrollbarWidth = window.innerWidth - document.body.clientWidth;
    removeHiddenClass(target);
    let togglers = [...document.querySelectorAll(`[data-target="${target.id}"]`)];
    togglers.forEach((toggler) => {
      setAriaExpanded(toggler);
      addActiveClass(toggler);
    });
    setTimeout(() => addActiveClass(target), 0);
    if (bodyScroll) {
      document.body.style.overflow = "hidden";
      headerInner.style.paddingRight = scrollbarWidth + "px";
    }
    if (isTrapFocus) {
      focusTarget(target);
    }
    if (!binder.isSet()) {
      binder.set();
    }
  }
  function closeToggleTarget(target, bodyScroll, timeout, isRemoveTrapFocus) {
    if (!target || !isTargetActive(target)) {
      return;
    }
    target.classList.remove(cssClasses.active);
    let togglers = [...document.querySelectorAll(`[data-target="${target.id}"]`)];
    togglers.forEach((toggler) => {
      removeAriaExpanded(toggler);
      removeActiveClass(toggler);
    });
    setTimeout(() => addHiddenClass(target), timeout);
    if (bodyScroll) {
      document.body.style.overflow = null;
      headerInner.style.paddingRight = "0px";
    }
    if (isRemoveTrapFocus) {
      removeFocusTarget();
    }
    binder.remove();
  }
  function addActiveClass(target) {
    target.classList.add(cssClasses.active);
  }
  function removeActiveClass(target) {
    target.classList.remove(cssClasses.active);
  }
  function addHiddenClass(target) {
    target.classList.add(cssClasses.hidden);
  }
  function removeHiddenClass(target) {
    target.classList.remove(cssClasses.hidden);
  }
  function toggleBoxShadow(isHidden) {
    header.classList.toggle(cssClasses.shadowHidden, isHidden);
  }
  function setAriaExpanded(toggler) {
    toggler.setAttribute(attributes.ariaExpanded, true);
  }
  function removeAriaExpanded(toggler) {
    toggler.setAttribute(attributes.ariaExpanded, false);
  }
  function setTabIndexOnTarget(target) {
    focusable(target).forEach((element) => {
      element.setAttribute(attributes.tabIndex, 0);
    });
  }
  function focusTarget(target) {
    if (!target) {
      return;
    }
    previouslySelectedElement = document.activeElement;
    const focusableElements = focusable(target);
    if (focusableElements.length) {
      window.setTimeout(() => trapFocus(target, { elementToFocus: focusableElements[0] }), 0);
      return;
    }
    trapFocus(target);
  }
  function removeFocusTarget() {
    if (isElement(previouslySelectedElement)) {
      window.setTimeout(() => previouslySelectedElement.focus(), 0);
    }
    removeTrapFocus();
  }
  function closeAllMenus(list, isRemoveTrapFocus, timeout) {
    if (hasActiveLocalizationPanel()) {
      closeLocalizationSelector();
    }
    if (timeout === void 0) {
      timeout = 200;
    }
    if (isRemoveTrapFocus === void 0) {
      isRemoveTrapFocus = true;
    }
    list.forEach((menu) => {
      closeToggleTarget(menu, true, timeout, isRemoveTrapFocus);
    });
  }
  function getActiveElements(list) {
    return list.filter((item) => isTargetActive(item));
  }
  function headerTopPositionHandler() {
    let condition = window.scrollY <= 0;
    if (condition && !header.classList.contains("header-section--top-position")) {
      header.classList.add("header-section--top-position");
    } else if (!condition && header.classList.contains("header-section--top-position")) {
      header.classList.remove("header-section--top-position");
    }
  }
  function scrollHandler() {
    let currentScrollPosition = document.documentElement.scrollTop || document.body.scrollTop;
    let condition = staticHeader ? currentScrollPosition > 0 : currentScrollPosition > 0 && lastScrollPosition <= currentScrollPosition;
    if (condition) {
      if (getComputedStyle(document.body).overflow !== "hidden" && (!header.matches(":hover") || !mediaQueryList.matches) && header.getBoundingClientRect().y + header.getBoundingClientRect().height < currentScrollPosition) {
        header.classList.add(cssClasses.collapsed);
        isHeaderHidden = true;
        window.themeCore.EventBus.emit("Toggle:headerToggleMenuDrawer:close");
      }
    } else {
      header.classList.remove(cssClasses.collapsed);
      isHeaderHidden = false;
    }
    lastScrollPosition = currentScrollPosition;
    if (hasActiveLocalizationPanel()) {
      closeLocalizationSelector();
    }
  }
  function closeLocalizationSelector() {
    const localizationForms = [...document.querySelectorAll(selectors.localizationForm)];
    localizationForms.forEach((form) => {
      const links = form.querySelectorAll(selectors.localizationLink);
      const button = form.querySelector(selectors.localizationButton);
      const panel = form.querySelector(selectors.localizationPanel);
      panel.setAttribute(attributes.hidden, "true");
      button.setAttribute(attributes.ariaExpanded, "false");
      links.forEach((link) => link.setAttribute("tabindex", -1));
    });
  }
  function hasActiveLocalizationPanel() {
    const localizationForms = [...document.querySelectorAll(selectors.localizationForm)];
    let active = false;
    localizationForms.forEach((form) => {
      let panel = form.querySelector(selectors.localizationPanel);
      if (!panel.hasAttribute(attributes.hidden)) {
        active = true;
      }
    });
    return active;
  }
  return Object.freeze({
    init,
    getHeaderHeight: () => headerHeight,
    getHeaderHeightStatic: () => headerHeightStatic
  });
};
const action = () => {
  window.themeCore.Header = window.themeCore.Header || Header();
  window.themeCore.utils.register(window.themeCore.Header, "header");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
