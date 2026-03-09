const selectors = {
  section: ".js-banner-with-scroll-images",
  column: ".js-banner-with-scroll-images-column"
};
const BannerWithScrollImages = () => {
  let sections = [];
  const isDesktop = window.matchMedia("(min-width: 991.98px)");
  function init(sectionId) {
    sections = [...document.querySelectorAll(selectors.section)].filter((section) => !sectionId || section.closest(`#shopify-section-${sectionId}`));
    isDesktop.addEventListener("change", handleMedia);
    handleMedia(isDesktop);
  }
  function handleMedia(media) {
    if (media.matches) {
      window.addEventListener("scroll", scrollAnimation);
      scrollAnimation();
    } else {
      window.removeEventListener("scroll", scrollAnimation);
      removeAttribute();
    }
  }
  function scrollAnimation() {
    const intersectionObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && isDesktop.matches) {
          const columns = entry.target.querySelectorAll(selectors.column);
          const position = window.scrollY - entry.target.offsetTop + window.innerHeight;
          const speed = 0.5;
          if (columns.length > 0) {
            columns.forEach((column, index) => {
              let translateYPosition;
              if (index !== 1) {
                translateYPosition = `${position * speed}px`;
              } else {
                translateYPosition = `-${position * speed}px`;
              }
              column.style.transform = `translateY(${translateYPosition})`;
            });
          }
        }
      });
    });
    if (sections.length > 0) {
      sections.forEach((section) => {
        intersectionObserver.observe(section);
      });
    }
  }
  function removeAttribute() {
    sections.forEach((section) => {
      const columns = section.querySelectorAll(selectors.column);
      if (columns.length > 0) {
        columns.forEach((column) => {
          column.removeAttribute("style");
        });
      }
    });
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.BannerWithScrollImages = window.themeCore.BannerWithScrollImages || BannerWithScrollImages();
  window.themeCore.utils.register(window.themeCore.BannerWithScrollImages, "banner-with-scroll-images");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
