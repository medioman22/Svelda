const PredictiveSearch = () => {
  const debounce = window.themeCore.utils.debounce;
  const globalClasses = window.themeCore.utils.cssClasses;
  const selectors = {
    form: ".js-predictive-search-form",
    input: ".js-predictive-search-input",
    resultContainer: ".js-predictive-search-result",
    searchType: "input[name='type']",
    applyButton: ".js-predictive-search-apply-button",
    resultRow: ".js-predictive-search-result-row",
    tabsButton: ".js-predictive-search-tabs-button",
    preloader: ".js-preloader",
    searchDrawer: "#headerDrawerSearch",
    resultWrapper: ".js-predictive-search-results",
    footer: ".js-predictive-search-footer",
    activeTab: ".js-predictive-search-tabs-button.is-active",
    tabsWrapper: ".js-predictive-search-tabs-wrapper",
    tabsItem: ".js-predictive-search-tabs-item"
  };
  const attributes = {
    disabled: "disabled",
    id: "id",
    dataId: "data-id",
    ariaExpanded: "aria-expanded",
    ariaHidden: "aria-hidden"
  };
  const classes = {
    visuallyHidden: "visually-hidden",
    ...globalClasses
  };
  const SEARCH_RESULTS_COUNT = 8;
  let cachedResults = {};
  const preloader = document.querySelector(selectors.preloader);
  const footer = document.querySelector(selectors.footer);
  const defaultResult = document.querySelector(selectors.resultContainer) ? document.querySelector(selectors.resultContainer).innerHTML : null;
  const locale = window.Shopify.routes.root;
  async function searchAction(event) {
    const input = event.target.closest(selectors.input);
    const searchDrawer = document.querySelector(selectors.searchDrawer);
    const resultContainer = document.querySelector(selectors.resultContainer);
    const applyButton = document.querySelector(selectors.applyButton);
    if (!searchDrawer || !input || !resultContainer || !applyButton) {
      return;
    }
    const inputValue = input.value.trim();
    if (!inputValue.length) {
      applyButton.setAttribute(attributes.disabled, attributes.disabled);
      applyButton.setAttribute(attributes.ariaHidden, "true");
      clearInnerResults(resultContainer);
      footer.classList.add(classes.hidden);
      resultContainer.innerHTML = defaultResult;
      return;
    }
    initPreloader();
    if (cachedResults[inputValue]) {
      renderResult(cachedResults[inputValue], resultContainer, applyButton);
      removePreloader();
      footer.classList.remove(classes.hidden);
      return;
    }
    const searchResponse = await getResult(inputValue);
    const responseText = new DOMParser().parseFromString(await searchResponse.text(), "text/html");
    cachedResults[inputValue] = responseText;
    renderResult(responseText, resultContainer, applyButton);
    removePreloader();
    footer.classList.remove(classes.hidden);
  }
  function resetAction() {
    const applyButton = document.querySelector(selectors.applyButton);
    const resultContainer = document.querySelector(selectors.resultContainer);
    applyButton.setAttribute(attributes.disabled, attributes.disabled);
    applyButton.setAttribute(attributes.ariaHidden, "true");
    clearInnerResults(resultContainer);
    resultContainer.innerHTML = defaultResult;
    footer.classList.add(classes.hidden);
  }
  function initPreloader() {
    if (!preloader) {
      return;
    }
    preloader.classList.add(classes.active);
  }
  function removePreloader() {
    if (!preloader) {
      return;
    }
    preloader.classList.remove(classes.active);
  }
  function renderResult(responseText, resultContainer, applyButton) {
    clearInnerResults(resultContainer);
    applyButton.removeAttribute(attributes.disabled);
    applyButton.removeAttribute(attributes.ariaHidden);
    const result = responseText.querySelector(selectors.resultWrapper);
    if (!result) {
      applyButton.setAttribute(attributes.disabled, attributes.disabled);
      applyButton.setAttribute(attributes.ariaHidden, "true");
      renderEmptyResult(resultContainer);
      return;
    }
    resultContainer.innerHTML = result.innerHTML;
    document.addEventListener("click", setActiveTabCategory);
  }
  function setActiveTabCategory(event) {
    const tabButtons = [...document.querySelectorAll(selectors.tabsButton)];
    const resultRows = [...document.querySelectorAll(selectors.resultRow)];
    const targetTabButton = event.target.closest(selectors.tabsButton);
    if (!targetTabButton || !tabButtons.length || !resultRows.length) {
      return;
    }
    tabButtons.forEach((button) => {
      button.classList.remove(classes.active);
      button.setAttribute(attributes.ariaExpanded, false);
    });
    targetTabButton.classList.add(classes.active);
    targetTabButton.setAttribute(attributes.ariaExpanded, true);
    resultRows.forEach((resultRow) => {
      resultRow.classList.remove(classes.active);
      resultRow.classList.add(classes.visuallyHidden);
    });
    resultRows.filter((resultRow) => resultRow.dataset.id === targetTabButton.dataset.id).forEach((resultRow) => {
      resultRow.classList.add(classes.active);
      resultRow.classList.remove(classes.visuallyHidden);
    });
    const tabsWrapper = targetTabButton.closest(selectors.tabsWrapper);
    const tabsWrapperOffset = tabsWrapper.offsetLeft + (parseInt(window.getComputedStyle(tabsWrapper).paddingLeft) || 0);
    const newActiveOffset = targetTabButton.offsetLeft;
    tabsWrapper.scrollTo({
      left: newActiveOffset - tabsWrapperOffset,
      behavior: "smooth"
    });
  }
  function renderEmptyResult(resultContainer) {
    var _a, _b, _c;
    const emptyResult = `
				<p class="h4 predictive-search__result-empty">
					${((_c = (_b = (_a = window.themeCore) == null ? void 0 : _a.objects) == null ? void 0 : _b.settings) == null ? void 0 : _c.predictive_search_no_result) || window.themeCore.translations.get("general.predictive_search.no_results")}
				</p>
			`;
    resultContainer.innerHTML += emptyResult;
  }
  async function getResult(inputValue) {
    const searchType = document.querySelector(selectors.searchType);
    if (!searchType) {
      return;
    }
    const resourcesType = `${encodeURIComponent("resources[type]")}=${searchType.value}`;
    const resourcesLimit = `${encodeURIComponent("resources[limit]")}=${SEARCH_RESULTS_COUNT}`;
    const url = `${locale}search/suggest?q=${encodeURIComponent(inputValue)}&${resourcesType}&${resourcesLimit}&section_id=predictive-search`;
    return await fetch(url);
  }
  function clearInnerResults(resultContainer) {
    resultContainer.innerHTML = "";
  }
  function onFormSubmit(event) {
    const form = event.target.closest(selectors.form);
    if (!form) {
      return;
    }
    event.preventDefault();
    const inputValue = form.querySelector(selectors.input).value.trim();
    if (!inputValue.length) {
      return;
    }
    searchRedirect(inputValue);
  }
  function searchRedirect(value) {
    const activeTab = document.querySelector(selectors.activeTab);
    if (!activeTab) {
      return;
    }
    const valueEncoded = encodeURI(value);
    const url = `${locale}search/?type=${activeTab.getAttribute(attributes.dataId)}&options%5Bprefix%5D=last&q=${valueEncoded}`;
    window.location.replace(url);
  }
  function init() {
    document.addEventListener("input", debounce(searchAction, 200, false));
    document.addEventListener("reset", resetAction);
    document.addEventListener("submit", onFormSubmit);
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.PredictiveSearch = window.themeCore.PredictiveSearch || PredictiveSearch();
  window.themeCore.utils.register(window.themeCore.PredictiveSearch, "predictive-search");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
