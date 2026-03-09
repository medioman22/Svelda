import { d as disableTabulationOnNotActiveSlidesWithModel } from "./disableTabulationOnNotActiveSlidesWithModel-38e80234.js";
const selectors = {
  container: "[data-js-product-form]",
  product: "[data-js-product-json]",
  sku: ".js-product-sku",
  price: ".js-price",
  productPrice: "[data-product-price]",
  productPriceOld: "[data-price-old]",
  priceUnit: "[data-js-unit-price]",
  variantId: '[name="id"]',
  submit: '[type="submit"]',
  quantityError: ".js-product-quantity-error",
  variants: "[data-js-product-variant]",
  isPreset: "[data-is-preset]",
  productInventory: "[data-product-inventory]",
  lowStockText: ".js-product-low-stock-msg",
  highStockText: ".js-product-high-stock-msg",
  additionalQuantityInput: "[data-quantity-input-additional]",
  swatchPreview: ".js-swatch-preview",
  stickyBar: ".js-sticky-add-to-cart",
  stickyBarButton: ".js-sticky-add-to-cart-button",
  recipientCheckbox: ".js-recipient-form-checkbox",
  recipientFieldsContainer: ".js-recipient-form-fields",
  recipientField: ".js-recipient-form-field",
  recipientTimeZoneOffset: ".js-recipient-form-timezone-offset",
  recipientNoJsControl: ".js-recipient-form-no-js-control",
  customFieldGroup: ".js-custom-field-block",
  customFieldInput: ".js-custom-field-input",
  customFieldCheckbox: ".js-custom-field-checkbox",
  animate: ".js-animate",
  breaksVal: ".js-price-breaks-val",
  volumePricing: ".js-product-volume-pricing",
  quantityRuleMin: ".js-product-quantity-rule-min",
  quantityRuleMax: ".js-product-quantity-rule-max",
  quantityRuleIncrement: ".js-product-quantity-rule-increment",
  quantityRuleMinVal: ".js-product-quantity-rule-min-val",
  quantityRuleMaxVal: ".js-product-quantity-rule-max-val",
  quantityRuleIncrementVal: ".js-product-quantity-rule-increment-val",
  volumePricingList: ".js-product-volume-pricing-list",
  volumePricingJSON: "[data-product-qty-breaks-json]",
  volumePricingShowMore: ".js-product-volume-pricing-show-more",
  priceVolume: ".js-price-volume",
  formError: ".js-form-error",
  swatchLabelName: ".js-swatch-label-name",
  quantityRules: ".js-product-quantity-rules",
  discountButton: ".js-discount-button",
  discountStatus: "[data-discount-button-status]",
  discountCode: ".js-discount-code"
};
let classes = {};
const attributes = {
  id: "id",
  isCurrencyEnabled: "data-currency-code-enabled",
  discountStatus: "data-discount-button-status"
};
const ProductForm = () => {
  let convertFormData;
  let QuantityWidget;
  let cssClasses;
  let formatMoney;
  let getUrlWithVariant;
  let containers = [];
  let forms = [];
  function init() {
    window.themeCore.utils.arrayIncludes;
    convertFormData = window.themeCore.utils.convertFormData;
    QuantityWidget = window.themeCore.utils.QuantityWidget;
    cssClasses = window.themeCore.utils.cssClasses;
    formatMoney = window.themeCore.utils.formatMoney;
    getUrlWithVariant = window.themeCore.utils.getUrlWithVariant;
    classes = {
      ...cssClasses,
      onSale: "price--on-sale",
      hidePrice: "price--hide",
      animate: "js-animate",
      animated: "animated"
    };
    containers = findForms();
    forms = setForms();
    setEventListeners();
    setEventBusListeners();
    initOptions();
    showOptions();
    initStickyBar();
    initRecipientForm();
    initDiscountCodeButton();
  }
  function setEventListeners() {
    forms.forEach(({ container: form }) => {
      form.addEventListener("change", onChangeForm);
      form.addEventListener("submit", onFormSubmit);
    });
    window.themeCore.EventBus.listen("cart:updated", function(cartData) {
      if (!cartData) {
        return;
      }
      if (!cartData.items) {
        return;
      }
      containers.forEach(function(container) {
        const variantSelector = container.querySelector("[name=id]");
        variantSelector.dispatchEvent(new Event("change", { bubbles: true }));
      });
    });
  }
  function setEventBusListeners() {
    if (forms.length) {
      forms.forEach(({ container: form }) => {
        window.themeCore.EventBus.listen(`form:${form.id}:change-variant`, updateForm);
      });
    }
  }
  function updateForm({ currentVariant, elements, form, product, isTrusted }) {
    updateOptions({
      product,
      elements,
      container: form
    });
    const quantityVariantInCart = getVariantCountInCart(currentVariant);
    if (isTrusted) {
      updateSwatchLabelName(currentVariant, form);
      updateSwatchPreview(currentVariant, form);
      updateSku(elements, currentVariant);
      updateSku({ skuContainer: elements.mobileSkuContainer }, currentVariant);
      updatePrice(elements, currentVariant);
      updateVariantId(elements, currentVariant);
      updateErrorMessages(elements);
      updateAddToCart(elements, currentVariant);
      updateStockStatus(form, currentVariant);
      updatePickupAvailability(currentVariant, form);
    }
    updateVolumePricing(form, currentVariant, quantityVariantInCart, isTrusted);
    updateQuantityRules(form, currentVariant);
    updateQuantityLabelCartCount(form, quantityVariantInCart);
  }
  function updatePickupAvailability(variant, form) {
    const pickUpAvailability = form.querySelector("pickup-availability");
    if (!pickUpAvailability) {
      return;
    }
    if (variant && variant.available) {
      pickUpAvailability.fetchAvailability(variant.id);
    } else {
      pickUpAvailability.removeAttribute("available");
      pickUpAvailability.innerHTML = "";
    }
  }
  function updateSwatchLabelName(variant, container) {
    const swatchNameEl = container.querySelector(selectors.swatchLabelName);
    if (!swatchNameEl) {
      return;
    }
    if (!variant) {
      const swatchName = swatchNameEl.getAttribute("data-swatch-name");
      const swatchOptionSelected = container.querySelector(`[data-option='${swatchName}']:checked`);
      if (swatchOptionSelected) {
        swatchNameEl.textContent = swatchOptionSelected.value;
      }
      return;
    }
    const optionPosition = swatchNameEl.getAttribute("data-swatch-position");
    const optionLabel = "option" + optionPosition;
    const optionName = variant[optionLabel];
    if (!optionName) {
      return;
    }
    swatchNameEl.textContent = optionName;
  }
  function updateSwatchPreview(variant, container) {
    const swatchPreviewEl = container.querySelector(selectors.swatchPreview);
    if (!swatchPreviewEl) {
      return;
    }
    const swatchName = swatchPreviewEl.getAttribute("data-swatch-name");
    const swatchOptionSelected = container.querySelector(`[data-option='${swatchName}']:checked`);
    if (!swatchOptionSelected) {
      return;
    }
    const swatchLabel = container.querySelector(`label[for='${swatchOptionSelected.id}']`);
    const swatchColor = swatchLabel.style.getPropertyValue("--swatch-color");
    const swatchImage = swatchLabel.style.getPropertyValue("--swatch-image");
    let swatchImageForPreview = swatchImage;
    if (swatchImage.includes("width=32")) {
      swatchImageForPreview = swatchImage.replace("width=32", "width=112").replace("height=32", "height=112");
    } else if (swatchImage.includes("width=60")) {
      swatchImageForPreview = swatchImage.replace("width=60", "width=112").replace("height=60", "height=112");
    } else if (swatchImage.includes("width=80")) {
      swatchImageForPreview = swatchImage.replace("width=80", "width=112").replace("height=80", "height=112");
    }
    if (!swatchImage) {
      swatchPreviewEl.style.setProperty("--swatch-color", swatchColor);
    } else {
      swatchPreviewEl.style.setProperty("--swatch-color", "");
    }
    swatchPreviewEl.style.setProperty("--swatch-image", swatchImageForPreview);
  }
  function updatePrice({ priceContainers }, variant) {
    if (!variant) {
      priceContainers.forEach((priceContainer) => priceContainer.classList.add(classes.hidePrice));
      updateUnitPrice(priceContainers, {});
      return;
    } else if (!priceContainers.length) {
      return;
    }
    priceContainers.forEach((priceContainer) => {
      const isCurrencyEnabled = priceContainer.hasAttribute(attributes.isCurrencyEnabled);
      const format = isCurrencyEnabled ? window.themeCore.objects.shop.money_with_currency_format : window.themeCore.objects.shop.money_format;
      const { price, compare_at_price } = variant;
      const onSale = compare_at_price > price;
      const moneyPrice = formatMoney(price, format);
      const moneyPriceOld = formatMoney(compare_at_price, format);
      priceContainer.classList.remove(classes.hidePrice);
      if (onSale) {
        priceContainer.classList.add(classes.onSale);
      } else {
        priceContainer.classList.remove(classes.onSale);
      }
      const productPrice = priceContainer.querySelectorAll(selectors.productPrice);
      const productPriceOld = priceContainer.querySelectorAll(selectors.productPriceOld);
      productPrice.forEach((element) => element.innerHTML = moneyPrice);
      productPriceOld.forEach((element) => element.innerHTML = moneyPriceOld);
    });
    updateUnitPrice(priceContainers, variant);
  }
  function updateUnitPrice(priceContainers, variant) {
    priceContainers.forEach((priceContainer) => {
      const unitPrice = [...priceContainer.querySelectorAll(selectors.priceUnit)];
      if (!unitPrice.length) {
        return;
      }
      const unitPriceContainerEl = unitPrice.find((element) => element.dataset.jsUnitPrice === "container");
      const unitPriceMoneyEl = unitPrice.find((element) => element.dataset.jsUnitPrice === "money");
      const unitPriceReferenceEl = unitPrice.find((element) => element.dataset.jsUnitPrice === "reference");
      const variantUnitPrice = variant.unit_price;
      const variantUnitPriceMeasurement = variant.unit_price_measurement;
      if (unitPriceMoneyEl) {
        if (variantUnitPrice) {
          const format = window.themeCore.objects.shop.money_format;
          unitPriceMoneyEl.innerHTML = formatMoney(variantUnitPrice, format);
        } else {
          unitPriceMoneyEl.innerHTML = "";
        }
      }
      if (unitPriceReferenceEl) {
        if (variantUnitPriceMeasurement) {
          const referenceValue = variantUnitPriceMeasurement.reference_value;
          const referenceUnit = variantUnitPriceMeasurement.reference_unit;
          unitPriceReferenceEl.innerHTML = referenceValue !== 1 ? referenceValue + referenceUnit : referenceUnit;
        } else {
          unitPriceReferenceEl.innerHTML = "";
        }
      }
      if (unitPriceContainerEl && (variantUnitPrice || variantUnitPriceMeasurement)) {
        unitPriceContainerEl.classList.remove(window.themeCore.utils.cssClasses.hidden);
      } else {
        unitPriceContainerEl.classList.add(window.themeCore.utils.cssClasses.hidden);
      }
    });
  }
  function updateSku({ skuContainer }, variant) {
    if (!skuContainer) {
      return;
    }
    let sku = null;
    if (variant) {
      sku = variant.sku;
    }
    if (!sku) {
      const isPreset = skuContainer.closest(selectors.isPreset);
      if (isPreset && isPreset.dataset.isPreset === "true") {
        return;
      }
      skuContainer.innerHTML = "";
      return;
    }
    const skuText = skuContainer.dataset.skuText;
    skuContainer.innerHTML = skuText ? skuText.replaceAll("{SKU}", sku).replaceAll("{sku}", sku) : sku;
  }
  function updateVariantId({ variantIdContainer }, variant) {
    if (!variantIdContainer || !variant) {
      return;
    }
    const { id } = variant;
    variantIdContainer.value = id;
  }
  function updateErrorMessages({ quantityError }) {
    if (!quantityError) {
      return;
    }
    quantityError.innerHTML = "";
  }
  function updateAddToCart({ submit }, currentVariant) {
    const removeDisabled = () => submit.forEach((button) => button.removeAttribute("disabled"));
    const setDisabled = () => submit.forEach((button) => button.setAttribute("disabled", "disabled"));
    const setSubmitText = (text) => submit.forEach((button) => button.innerText = text);
    const soldOut = window.themeCore.translations.get("products.product.sold_out");
    const unavailable = window.themeCore.translations.get("products.product.unavailable");
    const addToCart = window.themeCore.translations.get("products.product.add_to_cart");
    if (currentVariant && currentVariant.available) {
      removeDisabled();
      setSubmitText(addToCart);
    } else if (currentVariant && !currentVariant.available) {
      setDisabled();
      setSubmitText(soldOut);
    } else {
      setDisabled();
      setSubmitText(unavailable);
    }
  }
  function updateStockStatus(container, variant) {
    const productInventoryInfo = container.querySelector(selectors.productInventory);
    if (!productInventoryInfo) {
      return;
    }
    const lowStockTreshold = productInventoryInfo.getAttribute("data-low-stock-threshold");
    const lowStockMessage = container.querySelector(selectors.lowStockText);
    const highStockMessage = container.querySelector(selectors.highStockText);
    if (!variant || !variant.available) {
      highStockMessage.classList.add(window.themeCore.utils.cssClasses.hidden);
      lowStockMessage.classList.add(window.themeCore.utils.cssClasses.hidden);
      return;
    }
    const inventoryJSON = JSON.parse(productInventoryInfo.innerText);
    const currentInventory = inventoryJSON.find((variantInventory) => variantInventory.id === variant.id);
    const canSellAfterZero = currentInventory.inventory_policy === "continue" || currentInventory.inventory_management === null;
    if (!canSellAfterZero && currentInventory.inventory_quantity <= lowStockTreshold) {
      lowStockMessage.classList.remove(window.themeCore.utils.cssClasses.hidden);
      highStockMessage.classList.add(window.themeCore.utils.cssClasses.hidden);
    }
    if (currentInventory.inventory_quantity > lowStockTreshold || canSellAfterZero) {
      highStockMessage.classList.remove(window.themeCore.utils.cssClasses.hidden);
      lowStockMessage.classList.add(window.themeCore.utils.cssClasses.hidden);
    }
  }
  function updateQuantityRules(container, variant) {
    const currentContainerData = forms.find((form) => form.container === container);
    const quantityWidgetEl = currentContainerData.elements.quantityWidgetEl;
    const quantityRules = container.querySelector(selectors.quantityRules);
    if (!quantityRules) {
      return;
    }
    if (!variant || variant && !variant.quantity_rule) {
      quantityRules.classList.add(cssClasses.hidden);
      return;
    } else {
      quantityRules.classList.remove(cssClasses.hidden);
    }
    const variantQuantityRules = variant.quantity_rule;
    const quantityRuleIncrement = quantityRules.querySelector(selectors.quantityRuleIncrement);
    const quantityRuleMin = quantityRules.querySelector(selectors.quantityRuleMin);
    const quantityRuleMax = quantityRules.querySelector(selectors.quantityRuleMax);
    const quantityRuleIncrementVal = quantityRules.querySelector(selectors.quantityRuleIncrementVal);
    const quantityRuleMinVal = quantityRules.querySelector(selectors.quantityRuleMinVal);
    const quantityRuleMaxVal = quantityRules.querySelector(selectors.quantityRuleMaxVal);
    if (quantityRuleIncrementVal) {
      quantityRuleIncrementVal.textContent = window.themeCore.translations.get("products.product.increments_of", { number: variantQuantityRules.increment });
      quantityWidgetEl.setIncrement(variantQuantityRules.increment);
      variantQuantityRules.increment > 1 ? quantityRuleIncrement.classList.remove(cssClasses.hidden) : quantityRuleIncrement.classList.add(cssClasses.hidden);
    }
    if (quantityRuleMinVal) {
      quantityRuleMinVal.textContent = window.themeCore.translations.get("products.product.minimum_of", { number: variantQuantityRules.min });
      quantityWidgetEl.setMin(variantQuantityRules.min);
      quantityWidgetEl.toggleDecrease();
      quantityWidgetEl.toggleIncrease();
      variantQuantityRules.min > 1 ? quantityRuleMin.classList.remove(cssClasses.hidden) : quantityRuleMin.classList.add(cssClasses.hidden);
    }
    if (quantityRuleMaxVal) {
      if (variantQuantityRules.max !== null) {
        quantityRuleMaxVal.textContent = window.themeCore.translations.get("products.product.maximum_of", { number: variantQuantityRules.max });
        quantityRuleMax.classList.remove(cssClasses.hidden);
        quantityWidgetEl.setMax(variantQuantityRules.max);
      } else {
        quantityRuleMaxVal.textContent = "";
        quantityRuleMax.classList.add(cssClasses.hidden);
        quantityWidgetEl.setMax("");
      }
      quantityWidgetEl.toggleDecrease();
      quantityWidgetEl.toggleIncrease();
    }
    if (variantQuantityRules.increment < 2 && variantQuantityRules.min < 2 && variantQuantityRules.max === null) {
      quantityRules.classList.add(cssClasses.hidden);
    } else {
      quantityRules.classList.remove(cssClasses.hidden);
    }
  }
  function updateVolumePricing(container, variant, quantity, isTrusted) {
    const currentContainerData = forms.find((form) => form.container === container);
    const quantityWidgetEl = currentContainerData.elements.quantityWidgetEl;
    const currentVariantEl = container.querySelector("[name=id]");
    if (!currentVariantEl) {
      return;
    }
    const volumePricing = container.querySelector(selectors.volumePricing);
    const volumePricingList = container.querySelector(selectors.volumePricingList);
    const volumePricingJSONEl = container.querySelector(selectors.volumePricingJSON);
    let quantityBreaks = null;
    if (!volumePricingJSONEl || !volumePricing) {
      return;
    }
    if (variant) {
      const volumePricingJSON = JSON.parse(volumePricingJSONEl.innerHTML);
      quantityBreaks = volumePricingJSON[variant.id].quantity_price_breaks;
      updateVariantVolumePrice(quantityBreaks);
      if (!isTrusted) {
        return;
      }
      if (quantityBreaks.length) {
        renderVolumePriceList(quantityBreaks);
        volumePricing.classList.remove(cssClasses.hidden);
      } else {
        volumePricing.classList.add(cssClasses.hidden);
      }
    } else {
      volumePricing.classList.add(cssClasses.hidden);
    }
    function renderVolumePriceList(quantityBreaks2) {
      const showMoreBtn = container.querySelector(selectors.volumePricingShowMore);
      const moneyFormat = window.themeCore.objects.shop.money_with_currency_format;
      const priceTranslation = window.themeCore.translations.get("products.product.volume_pricing.each", {
        price: formatMoney(variant.price, moneyFormat)
      });
      showMoreBtn.addEventListener("click", function(e) {
        e.preventDefault();
        let listHiddenItems = volumePricingList.querySelectorAll(".is-hidden");
        if (!listHiddenItems.length) {
          return;
        }
        listHiddenItems.forEach(function(listItem) {
          listItem.classList.remove(cssClasses.hidden);
        });
        showMoreBtn.classList.add(cssClasses.hidden);
      });
      volumePricingList.innerHTML = "";
      let defaultMinPriceHTML = `
				<li class="product-volume-pricing__list-item">
					<span>${variant.quantity_rule.min}<span aria-hidden>+</span></span>
					<span>${priceTranslation}</span>
				</li>
			`;
      volumePricingList.insertAdjacentHTML("beforeend", defaultMinPriceHTML);
      quantityBreaks2.forEach(function(quantityBreak, i) {
        let hiddenClass = i >= 2 ? `${cssClasses.hidden}` : "";
        let quantityBreakHTML = `
					<li class="product-volume-pricing__list-item ${hiddenClass}">
						<span>${quantityBreak.minimum_quantity}<span aria-hidden>+</span></span>
						<span>${quantityBreak.price_each}</span>
					</li>
				`;
        volumePricingList.insertAdjacentHTML("beforeend", quantityBreakHTML);
      });
      if (quantityBreaks2.length >= 3) {
        showMoreBtn.classList.remove(cssClasses.hidden);
      } else {
        showMoreBtn.classList.add(cssClasses.hidden);
      }
    }
    function updateVariantVolumePrice(quantityBreaks2) {
      const priceEls = container.querySelectorAll(selectors.priceVolume);
      const moneyFormat = window.themeCore.objects.shop.money_with_currency_format;
      const priceTranslation = window.themeCore.translations.get("products.product.volume_pricing.price_at_each", {
        price: formatMoney(variant.price, moneyFormat)
      });
      if (!priceEls.length) {
        return;
      }
      if (!variant) {
        priceEls.forEach((el) => el.classList.add(cssClasses.hidden));
        return;
      }
      if (!quantityBreaks2 || !quantityBreaks2.length) {
        priceEls.forEach((el) => el.innerHTML = priceTranslation);
        priceEls.forEach((el) => el.classList.remove(cssClasses.hidden));
        return;
      }
      const currentBreak = quantityBreaks2.findLast((qtyBreak) => {
        return Number(quantity) + Number(quantityWidgetEl.quantity.value) >= qtyBreak.minimum_quantity;
      });
      if (!currentBreak) {
        priceEls.forEach((el) => el.innerHTML = priceTranslation);
        priceEls.forEach((el) => el.classList.remove(cssClasses.hidden));
        return;
      }
      priceEls.forEach((el) => el.innerHTML = currentBreak.price_at_each);
      priceEls.forEach((el) => el.classList.remove(cssClasses.hidden));
    }
  }
  function getVariantCountInCart(variant) {
    const cartData = window.themeCore.cartObject;
    if (!cartData || !variant) {
      return;
    }
    if (!cartData.items.length) {
      return 0;
    }
    const currentVariant = cartData.items.find(function(item) {
      return item.variant_id === variant.id;
    });
    if (!currentVariant) {
      return 0;
    }
    return currentVariant.quantity;
  }
  function updateQuantityLabelCartCount(container, quantity) {
    if (!container) {
      return;
    }
    const priceBreaksEl = container.querySelector(selectors.breaksVal);
    if (!priceBreaksEl) {
      return;
    }
    priceBreaksEl.classList.toggle(cssClasses.hidden, !quantity);
    if (!quantity) {
      priceBreaksEl.innerHTML = "";
    }
    priceBreaksEl.innerHTML = window.themeCore.translations.get("products.product.quantity_in_cart", { quantity });
  }
  function onChangeForm({ currentTarget: form, target, isTrusted }) {
    const currentFormEntity = forms.find(({ container, elements: { optionElements } }) => form === container && (optionElements.includes(target) || target.name === "id"));
    if (!currentFormEntity) {
      return;
    }
    currentFormEntity.findVariant = {
      isId: target.name === "id",
      target
    };
    currentFormEntity.isTrusted = isTrusted;
    findCurrentVariant(currentFormEntity);
  }
  function validateCustomFields(arr) {
    let error = false;
    arr.forEach(function(obj) {
      const inputValue = obj.input.value.trim();
      if (obj.checkbox) {
        if (obj.checkbox.checked && !inputValue.length) {
          obj.input.classList.add("error");
          obj.checkbox.classList.remove("error");
          error = true;
        } else if (!obj.checkbox.checked && inputValue.length) {
          obj.input.classList.remove("error");
          obj.checkbox.classList.add("error");
          error = true;
        } else {
          obj.input.classList.remove("error");
          obj.checkbox.classList.remove("error");
        }
      }
    });
    return error;
  }
  function onFormSubmit(event) {
    const target = event.target;
    event.preventDefault();
    const form = forms.find((f) => f.id === target.getAttribute(attributes.id));
    const customFieldElementsArr = form.elements.customFieldElements;
    if (customFieldElementsArr) {
      let isError = validateCustomFields(customFieldElementsArr);
      if (isError) {
        return;
      }
    }
    if (form) {
      const { submit } = form.elements;
      submit.forEach((button) => button.classList.add(classes.loading));
    }
    const formData = new FormData(target);
    const serialized = convertFormData(formData);
    window.themeCore.CartApi.makeRequest(window.themeCore.CartApi.actions.ADD_TO_CART, serialized).then((response) => {
      onFormSubmitSuccess(response, form);
    }).catch((error) => {
      onFormSubmitError(error, form);
    });
  }
  function onFormSubmitSuccess(success, form) {
    if (!form) {
      return;
    }
    const formElement = form.container;
    const { quantityWidget, submit } = form.elements;
    quantityWidget && quantityWidget.setValue(0);
    submit.forEach((button) => button.classList.remove(classes.loading));
    resetRecipientForm(formElement);
    window.themeCore.CartApi.makeRequest(window.themeCore.CartApi.actions.GET_CART);
  }
  function onFormSubmitError(error, form) {
    if (!form) {
      return;
    }
    const formElement = form.container;
    const hasRecipientForm = formElement.querySelector(selectors.recipientCheckbox);
    let { description } = error;
    const { quantityError, submit } = form.elements;
    if (typeof description === "object" && hasRecipientForm) {
      const sectionID = form.container.dataset.sectionId;
      let errors = error.errors;
      const errorMessages = formElement.querySelectorAll(selectors.formError);
      const recipientFormFields = formElement.querySelectorAll(selectors.recipientField);
      if (errorMessages.length && recipientFormFields.length) {
        errorMessages.forEach(function(messageEl) {
          messageEl.classList.add(classes.hidden);
          messageEl.innerText = "";
        });
        recipientFormFields.forEach(function(field) {
          field.setAttribute("aria-invalid", false);
          field.removeAttribute("aria-describedby");
        });
      }
      return Object.entries(errors).forEach(([key, value]) => {
        const errorMessageId = `RecipientForm-${key}-error-${sectionID}`;
        const errorMessageElement = formElement.querySelector(`#${errorMessageId}`);
        const inputId = `Recipient-${key}-${sectionID}`;
        const inputElement = formElement.querySelector(`#${inputId}`);
        let message = `${value.join(", ")}`;
        if (key === "send_on") {
          message = `${value.join(", ")}`;
        }
        if (errorMessageElement) {
          errorMessageElement.innerText = message;
          errorMessageElement.classList.remove(classes.hidden);
        }
        if (inputElement) {
          inputElement.setAttribute("aria-invalid", true);
          inputElement.setAttribute("aria-describedby", errorMessageId);
        }
        submit.forEach((button) => button.classList.remove(classes.loading));
      });
    }
    quantityError && (quantityError.innerHTML = description);
    submit.forEach((button) => button.classList.remove(classes.loading));
  }
  function findCurrentVariant({ container: form, product, elements, findVariant, isTrusted = true }) {
    const variants = product.variants;
    const formData = new FormData(form);
    const sectionId = form.dataset.sectionId;
    let currentVariant;
    const optionKeys = [...formData.keys()].filter((key) => key.startsWith("option"));
    let options = {};
    optionKeys.forEach((key) => options[key] = formData.get(key));
    if (Object.keys(options).some((key) => options[key])) {
      currentVariant = variants.find((variant) => Object.keys(options).every((key) => options[key] === variant[key]));
    } else if (findVariant && findVariant.isId) {
      currentVariant = variants.find((variant) => Number(findVariant.target.value) === variant.id);
    } else {
      return;
    }
    window.themeCore.EventBus.emit(`form:${form.id}:change-variant`, {
      form,
      product,
      currentVariant,
      elements,
      isTrusted
    });
    if (currentVariant) {
      window.themeCore.EventBus.emit(`pdp:section-${sectionId}:change-variant`, {
        variantId: currentVariant.id,
        variant: currentVariant,
        product
      });
      document.dispatchEvent(
        new CustomEvent("product:variant:change", {
          detail: currentVariant.id
        })
      );
    } else {
      document.dispatchEvent(
        new CustomEvent("product:variant:change", {
          detail: null
        })
      );
    }
    if (isEnableHistoryState(form)) {
      updateHistoryState(currentVariant);
    }
  }
  function updateHistoryState(variant) {
    if (!variant) {
      return null;
    }
    const url = getUrlWithVariant(window.location.href, variant.id);
    window.history.replaceState({ path: url }, "", url);
  }
  function isEnableHistoryState(form) {
    return form.dataset.enableHistoryState || false;
  }
  function initOptions() {
    forms.forEach((form) => {
      updateOptions(form);
      findCurrentVariant(form);
    });
  }
  function updateOptions(form) {
    const {
      product,
      elements: { optionElements },
      container
    } = form;
    const formData = new FormData(container);
    const selected = {
      option1: null,
      option2: null,
      option3: null
    };
    for (const [key, value] of formData.entries()) {
      if (Object.keys(selected).includes(key)) {
        selected[key] = value;
      }
    }
    const existingOptions = Object.keys(selected).filter((key) => selected[key]);
    existingOptions.forEach((option, index) => {
      const currentElements = optionElements.filter(({ name }) => option === name);
      currentElements.forEach((currentElement) => {
        const { value, name } = currentElement;
        const variantOptions = {};
        product.options.forEach((option2, currentIndex) => {
          const key = `option${currentIndex + 1}`;
          if (currentIndex < index) {
            variantOptions[key] = selected[key];
          }
        });
        variantOptions[name] = value;
        const availableVariant = product.variants.find((variant) => Object.keys(variantOptions).every((key) => variantOptions[key] === variant[key]) && variant.available);
        setAvailable(currentElement, !!availableVariant);
      });
    });
  }
  function setAvailable(input, available) {
    let label = input.nextElementSibling;
    if (input.matches("select")) {
      return;
    }
    if (available) {
      label.classList.remove(cssClasses.disabled);
    } else {
      label.classList.add(cssClasses.disabled);
    }
  }
  function findForms() {
    return [...document.querySelectorAll(selectors.container)];
  }
  function setForms() {
    return containers.reduce((acc, container) => {
      const productJsonTag = container.querySelector(selectors.product);
      let product = {};
      try {
        product = JSON.parse(productJsonTag.innerHTML);
      } catch (e) {
        return acc;
      }
      const id = container.getAttribute(attributes.id);
      const submit = [...container.querySelectorAll(selectors.submit)];
      const skuContainer = container.querySelector(selectors.sku);
      const priceContainers = [...container.querySelectorAll(selectors.price)];
      const quantityError = container.querySelector(selectors.quantityError);
      const variantIdContainer = container.querySelector(selectors.variantId);
      const optionElements = [...container.querySelectorAll("[data-option]")];
      let mobileSkuContainer = null;
      const additionalQuantityInput = container.querySelector(selectors.additionalQuantityInput);
      const quantityWidgetEl = QuantityWidget(container, {
        onQuantityChange: (widget) => {
          updateErrorMessages({ quantityError });
          variantIdContainer.dispatchEvent(new Event("change", { bubbles: true }));
          additionalQuantityInput && (additionalQuantityInput.value = widget.quantity.value);
        }
      }).init();
      additionalQuantityInput && additionalQuantityInput.addEventListener("input", () => {
        if (additionalQuantityInput.value !== quantityWidgetEl.value) {
          quantityWidgetEl.setValue(additionalQuantityInput.value);
          quantityWidgetEl.dispatch();
        }
      });
      const customFieldBlocks = [...container.querySelectorAll(selectors.customFieldGroup)];
      const customFieldElements = customFieldBlocks.map(function(customFieldBlock) {
        let input = customFieldBlock.querySelector(selectors.customFieldInput);
        let checkbox = customFieldBlock.querySelector(selectors.customFieldCheckbox);
        return {
          input,
          checkbox
        };
      });
      return [
        ...acc,
        {
          id,
          container,
          product,
          elements: {
            skuContainer,
            priceContainers,
            quantityWidgetEl,
            quantityError,
            variantIdContainer,
            submit,
            mobileSkuContainer,
            optionElements,
            customFieldElements
          }
        }
      ];
    }, []);
  }
  function initStickyBar() {
    containers.forEach((form) => {
      const stickyBar = form.querySelector(selectors.stickyBar);
      const mainButton = form.querySelector(selectors.submit);
      if (!stickyBar || !mainButton) {
        return;
      }
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          const rect = mainButton.getBoundingClientRect();
          stickyBar.classList.toggle(window.themeCore.utils.cssClasses.active, !entry.isIntersecting && rect.bottom < 0);
          if (!entry.isIntersecting) {
            const animate = stickyBar.closest(selectors.animate);
            animate && animate.classList.remove(classes.animate);
            animate && animate.classList.add(classes.animated);
          }
        });
      }, {});
      observer.observe(mainButton);
      stickyBar.addEventListener("click", (event) => {
        const stickyBarButton = event.target.closest(selectors.stickyBarButton);
        if (!stickyBarButton) {
          return;
        }
        mainButton.focus();
      });
    });
  }
  function initRecipientForm() {
    containers.forEach((form) => {
      const recipientCheckbox = form.querySelector(selectors.recipientCheckbox);
      const recipientFormFieldsContainer = form.querySelector(selectors.recipientFieldsContainer);
      const recipientFormFields = form.querySelectorAll(selectors.recipientField);
      const recipientTimeZoneOffset = form.querySelector(selectors.recipientTimeZoneOffset);
      const recipientControlNoJsCheckbox = form.querySelector(selectors.recipientNoJsControl);
      if (!recipientCheckbox || !recipientFormFieldsContainer || !recipientFormFields || !recipientTimeZoneOffset) {
        return;
      }
      recipientTimeZoneOffset.value = (/* @__PURE__ */ new Date()).getTimezoneOffset().toString();
      recipientControlNoJsCheckbox.disabled = true;
      recipientCheckbox.disabled = false;
      disableInputFields();
      recipientCheckbox.addEventListener("change", function() {
        if (recipientCheckbox.checked) {
          recipientFormFieldsContainer.classList.remove(classes.hidden);
          enableInputFields();
        } else {
          recipientFormFieldsContainer.classList.add(classes.hidden);
          disableInputFields();
        }
      });
      function disableInputFields() {
        recipientFormFields.forEach(function(field) {
          field.disabled = true;
        });
        recipientTimeZoneOffset.disabled = true;
      }
      function enableInputFields() {
        recipientFormFields.forEach(function(field) {
          field.disabled = false;
        });
        recipientTimeZoneOffset.disabled = false;
      }
    });
  }
  function recipientFormClearErrors(form) {
    const recipientCheckbox = form.querySelector(selectors.recipientCheckbox);
    if (!recipientCheckbox) {
      return;
    }
    const recipientFormFieldsContainer = form.querySelector(selectors.recipientFieldsContainer);
    const errorMessages = recipientFormFieldsContainer.querySelectorAll(selectors.formError);
    const recipientFormFields = form.querySelectorAll(selectors.recipientField);
    if (!errorMessages || !recipientFormFields) {
      return;
    }
    errorMessages.forEach(function(messageEl) {
      messageEl.classList.add(classes.hidden);
      messageEl.innerText = "";
    });
    recipientFormFields.forEach(function(field) {
      field.setAttribute("aria-invalid", false);
      field.removeAttribute("aria-describedby");
    });
  }
  function recipientFormClearInputs(form) {
    const recipientCheckbox = form.querySelector(selectors.recipientCheckbox);
    if (!recipientCheckbox) {
      return;
    }
    const recipientFormFields = form.querySelectorAll(selectors.recipientField);
    if (!recipientFormFields) {
      return;
    }
    recipientFormFields.forEach(function(field) {
      field.value = "";
    });
  }
  function resetRecipientForm(form) {
    const recipientCheckbox = form.querySelector(selectors.recipientCheckbox);
    if (!recipientCheckbox) {
      return;
    }
    if (recipientCheckbox.checked) {
      recipientCheckbox.checked = false;
      recipientCheckbox.dispatchEvent(new Event("change"));
      recipientFormClearErrors(form);
      recipientFormClearInputs(form);
    }
  }
  function showOptions() {
    containers.forEach((form) => {
      const variants = form.querySelector(selectors.variants);
      if (variants && variants.dataset.jsProductVariant !== "no-hidden") {
        variants.classList.add(cssClasses.hidden);
        variants.addEventListener("change", () => {
        });
      }
    });
  }
  function initDiscountCodeButton() {
    containers.forEach((form) => {
      const button = form.querySelector(selectors.discountButton);
      let isCopied = false;
      button == null ? void 0 : button.addEventListener("click", () => {
        if (!isCopied) {
          const discountElements = form.querySelectorAll(selectors.discountStatus);
          const discountCode = form.querySelector(selectors.discountCode);
          const tempTextArea = document.createElement("textarea");
          tempTextArea.value = discountCode.textContent;
          document.body.appendChild(tempTextArea);
          tempTextArea.select();
          document.execCommand("copy");
          document.body.removeChild(tempTextArea);
          discountElements.forEach((element) => {
            const isActive = element.getAttribute(attributes.discountStatus) === "active";
            element.classList.toggle(cssClasses.hidden, !isActive);
          });
          isCopied = true;
        }
      });
    });
  }
  function allForms() {
    return forms;
  }
  return Object.freeze({
    init,
    allForms
  });
};
const ProductCarousel = ({ config, selectors: selectors2, sectionId }) => {
  const Swiper = window.themeCore.utils.Swiper;
  const extendDefaults = window.themeCore.utils.extendDefaults;
  const defaultSelectors = {
    slider: ".js-product-media-slider",
    sliderNavigationNext: ".js-product-media-slider-next",
    sliderNavigationPrev: ".js-product-media-slider-prev",
    thumbNavigationNext: ".js-product-media-thumb-next",
    thumbNavigationPrev: ".js-product-media-thumb-prev",
    sliderSlideVariantId: ".js-product-gallery-slide-variant",
    sliderThumbnails: ".js-product-media-slider-thumbnails",
    activeClass: ".swiper-slide-active",
    modelPoster: ".js-product-media-model-poster",
    notInitedIframe: ".js-video.js-video-youtube, .js-video:empty"
  };
  selectors2 = extendDefaults(defaultSelectors, selectors2);
  let Slider = null;
  let Thumbnails = null;
  let initiated = false;
  function init() {
    if (initiated) {
      return Slider;
    }
    const mainSlider = document.querySelector(selectors2.slider);
    const sliderThumbnails = document.querySelector(selectors2.sliderThumbnails);
    let sliderAutoHeight = mainSlider.dataset.autoHeight;
    const thumbnailsPosition = sliderThumbnails.dataset.thumbnailsPosition;
    let thumbnailsDirections = "horizontal";
    if (thumbnailsPosition === "right") {
      thumbnailsDirections = "vertical";
    }
    if (thumbnailsDirections === "horizontal") {
      Thumbnails = new Swiper(selectors2.sliderThumbnails, {
        direction: thumbnailsDirections,
        slidesPerView: 6,
        spaceBetween: 4,
        freeMode: true,
        watchSlidesProgress: true,
        a11y: {
          slideRole: ""
        },
        threshold: 10,
        breakpoints: {
          1200: {
            slidesPerView: 6,
            spaceBetween: 16
          }
        }
      });
    } else {
      Thumbnails = new Swiper(selectors2.sliderThumbnails, {
        direction: "horizontal",
        slidesPerView: 6,
        spaceBetween: 4,
        freeMode: true,
        watchSlidesProgress: true,
        threshold: 10,
        breakpoints: {
          1200: {
            direction: thumbnailsDirections,
            slidesPerView: "auto",
            spaceBetween: 16
          }
        }
      });
    }
    Thumbnails.$el.on("keydown", (e) => {
      if (e.keyCode !== 13 && e.keyCode !== 32) {
        return;
      }
      const slideIndex = e.target.dataset.slideIndex;
      if (!slideIndex)
        return;
      Thumbnails.slideTo(slideIndex);
      Slider.slideTo(slideIndex);
    });
    let prevArrow = document.querySelector(selectors2.sliderNavigationPrev);
    let nextArrow = document.querySelector(selectors2.sliderNavigationNext);
    document.querySelector(selectors2.slider).getAttribute("data-dynamic-pagination");
    sliderAutoHeight = sliderAutoHeight === "true";
    Slider = new Swiper(selectors2.slider, {
      ...config,
      autoHeight: sliderAutoHeight,
      spaceBetween: 8,
      navigation: {
        nextEl: nextArrow,
        prevEl: prevArrow
      },
      thumbs: {
        swiper: Thumbnails
      }
    });
    let thumbPrevButton = document.querySelector(selectors2.thumbNavigationPrev);
    let thumbNextButton = document.querySelector(selectors2.thumbNavigationNext);
    if (thumbnailsDirections === "vertical" && thumbPrevButton && thumbNextButton) {
      Slider.on("slideChange", function() {
        if (this.activeIndex === 0) {
          thumbPrevButton.setAttribute("disabled", "");
          thumbPrevButton.classList.add("swiper-button-disabled");
        } else {
          thumbPrevButton.removeAttribute("disabled");
          thumbPrevButton.classList.remove("swiper-button-disabled");
        }
        if (this.slides.length - 1 === this.activeIndex) {
          thumbNextButton.setAttribute("disabled", "");
          thumbNextButton.classList.add("swiper-button-disabled");
        } else {
          thumbNextButton.removeAttribute("disabled", "");
          thumbNextButton.classList.remove("swiper-button-disabled");
        }
      });
      thumbPrevButton.addEventListener("click", function() {
        Slider.slidePrev();
      });
      thumbNextButton.addEventListener("click", function() {
        Slider.slideNext();
      });
    }
    Slider.on("slideChange", function(swiper) {
      const activeSlide = swiper.slides[swiper.activeIndex];
      if (!activeSlide) {
        return;
      }
      swiper.allowTouchMove = !(activeSlide.hasAttribute("data-model-slide") && !activeSlide.querySelector(selectors2.modelPoster));
    });
    const targetNode = document.querySelector(selectors2.slider);
    const observer = new MutationObserver(() => {
      if (targetNode.querySelector(selectors2.notInitedIframe)) {
        return;
      }
      disableTabulationOnNotActiveSlidesWithModel(Slider);
      observer.disconnect();
    });
    const observerOptions = {
      attributes: true,
      childList: true,
      subtree: true
    };
    observer.observe(targetNode, observerOptions);
    setEventBusListeners();
    initiated = true;
  }
  function setEventBusListeners() {
    if (!Slider) {
      return;
    }
    Slider.on("slideChange", function(swiper) {
      window.themeCore.EventBus.emit("product-slider:slide-change");
      disableTabulationOnNotActiveSlidesWithModel(swiper);
    });
    window.themeCore.EventBus.listen(`pdp:section-${sectionId}:change-variant`, onChangeVariant);
  }
  function onChangeVariant({ variantId }) {
    if (!Slider) {
      return;
    }
    const currentIndex = [...Slider.slides].findIndex((slide) => {
      const slideVariantIdEl = slide.querySelector(selectors2.sliderSlideVariantId);
      if (!slideVariantIdEl) {
        return false;
      }
      const slideVariantIds = slideVariantIdEl.dataset.variantId;
      return slideVariantIds.includes(variantId);
    });
    if (!currentIndex && currentIndex !== 0) {
      return;
    }
    Slider.slideTo(currentIndex);
  }
  function destroy() {
    if (Slider && initiated) {
      Slider.destroy();
      Slider = null;
    }
    if (Thumbnails && initiated) {
      Thumbnails.destroy();
      Thumbnails = null;
    }
    initiated = false;
  }
  function disableSwipe() {
    Slider.allowTouchMove = false;
  }
  return Object.freeze({
    init,
    destroy,
    disableSwipe
  });
};
export {
  ProductCarousel as P,
  ProductForm as a
};
