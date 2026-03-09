const SearchTemplate = () => {
  const cssClasses = {
    ...window.themeCore.utils.cssClasses,
    animated: "animated"
  };
  const attributes = {
    searchType: "data-search-type",
    gridCol: "data-grid-cols",
    type: "data-type"
  };
  const selectors = {
    section: ".js-search",
    tabButton: `[${attributes.searchType}]`,
    resultCounter: ".js-search-result-counter",
    reset: ".js-search-reset",
    input: ".js-search-input",
    searchTypeInput: ".js-search-types",
    gridViewButton: ".js-grid-view-btn",
    gridViewButtons: ".js-grid-view-buttons",
    grid: ".js-grid-wrapper",
    searchBody: ".js-search-body",
    typesWrapper: ".js-search-types-wrapper"
  };
  async function init() {
    const ProductFilters = await window.themeCore.utils.getExternalUtil(
      "ProductFilters"
    );
    const section = document.querySelector(selectors.section);
    ProductFilters(section).init();
    const input = section.querySelector(selectors.input);
    await initButtons(section);
    window.themeCore.EventBus.listen("compare-products:init", () => {
      initButtons(section);
    });
    section.addEventListener("click", (event) => {
      const reset = event.target.closest(selectors.reset);
      if (!reset || !input) {
        return;
      }
      event.preventDefault();
      input.value = "";
    });
    const gridViewButtons = [...section.querySelectorAll(selectors.gridViewButton)];
    if (gridViewButtons.length > 0) {
      initGridViewButtons(gridViewButtons);
    }
    section.classList.add(cssClasses.animated);
  }
  async function initButtons(section) {
    let url = new URL(window.location.href);
    url.searchParams.set("view", "count");
    const tabButtons = section.querySelectorAll(selectors.tabButton);
    const currentButton = [...tabButtons].find((button) => button.classList.contains(cssClasses.active));
    if (currentButton) {
      const buttonsWrapper = currentButton.closest(selectors.typesWrapper);
      const newActiveOffset = currentButton.offsetLeft;
      buttonsWrapper.scrollTo({
        left: newActiveOffset,
        behavior: "smooth"
      });
    }
    let allResults = 0;
    for (const tabButton of tabButtons) {
      const type = tabButton.getAttribute(attributes.searchType);
      if (type !== "product") {
        const query = url.searchParams.get("q");
        url = new URL(url.origin + url.pathname);
        url.searchParams.set("view", "count");
        url.searchParams.set("q", query);
      }
      url.searchParams.set("type", type);
      try {
        const res = await fetch(url.toString());
        const data = await res.text();
        tabButton.innerText = window.themeCore.translations.get(`sections.search_template.${type}s`, { count: data });
        allResults += +data;
      } catch (e) {
        console.log(e);
      } finally {
        const searchType = document.querySelector(selectors.searchTypeInput).value;
        if (type === "product" && (searchType == null ? void 0 : searchType.split(",").length) !== 1) {
          tabButton.click();
          tabButton.classList.add(cssClasses.active);
          const searchBody = section.querySelector(selectors.searchBody);
          searchBody == null ? void 0 : searchBody.classList.remove(cssClasses.hidden);
        }
      }
    }
    const resultCounter = section.querySelector(selectors.resultCounter);
    if (resultCounter) {
      resultCounter.innerText = window.themeCore.translations.get(`general.search.results_with_count.${allResults === 1 ? "one" : "other"}`, { count: allResults, terms: url.searchParams.get("q") });
    }
  }
  function initGridViewButtons(gridButtons) {
    const productsGrid = document.querySelector(selectors.grid);
    const customerGridView = localStorage.getItem("search-grid-cols");
    const defaultButton = gridButtons.find((button) => +button.dataset.gridCols === 4);
    if (customerGridView) {
      const activeButton = gridButtons.find((button) => button.dataset.gridCols === customerGridView);
      productsGrid.setAttribute(attributes.gridCol, customerGridView);
      defaultButton.classList.remove(cssClasses.active);
      activeButton.classList.add(cssClasses.active);
    }
    gridButtons.forEach(function(button) {
      button.addEventListener("click", function() {
        const gridView = button.getAttribute(attributes.gridCol);
        if (button.classList.contains(cssClasses.active)) {
          return;
        }
        const currentActive = [...gridButtons].find((el) => el.classList.contains(cssClasses.active));
        const newActive = button;
        currentActive.classList.remove(cssClasses.active);
        newActive.classList.add(cssClasses.active);
        productsGrid.setAttribute(attributes.gridCol, gridView);
        if (gridView === "3" || gridView === "2") {
          localStorage.setItem("search-grid-cols", gridView);
        } else {
          localStorage.removeItem("search-grid-cols");
        }
      });
    });
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.SearchTemplate = window.themeCore.SearchTemplate || SearchTemplate();
  window.themeCore.utils.register(window.themeCore.SearchTemplate, "search-template");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
