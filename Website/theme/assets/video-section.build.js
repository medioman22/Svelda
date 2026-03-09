const Video = (videoContainer) => {
  const Video2 = window.themeCore.utils.Video;
  const VIDEO_TYPES = window.themeCore.utils.VIDEO_TYPES;
  const cssClasses = window.themeCore.utils.cssClasses;
  const mobileSize = window.matchMedia("(max-width: 767px)");
  const selectors2 = {
    iframe: "iframe",
    videoContainer: ".js-video-section",
    startButton: ".js-video-start-button",
    videoPlaceholder: ".js-video-placeholder",
    mobileVideoPlayer: "video__player--mobile",
    section: "[data-section-id]"
  };
  const attributes2 = {
    sectionId: "data-section-id",
    type: "data-type"
  };
  const config = {
    videoContainer,
    options: {
      youtube: {
        autoplay: 0,
        controls: 1,
        showinfo: 0,
        rel: 0,
        playsinline: 1,
        loop: 0
      },
      vimeo: {
        controls: true,
        loop: false,
        muted: true,
        portrait: false,
        title: false,
        keyboard: false,
        byline: false,
        autopause: false
      }
    }
  };
  let videos;
  const startButton = videoContainer.querySelector(selectors2.startButton);
  videoContainer.querySelector(
    selectors2.videoPlaceholder
  );
  function initVideos(config2) {
    return Video2(config2).init();
  }
  function playVideo(player, type) {
    switch (type) {
      case VIDEO_TYPES.html: {
        player.play();
        break;
      }
      case VIDEO_TYPES.vimeo: {
        player.play();
        break;
      }
      case VIDEO_TYPES.youtube: {
        player.mute();
        player.playVideo();
        break;
      }
      default:
        return;
    }
  }
  function pauseVideo(video) {
    if (video.type === "youtube") {
      video.player.pauseVideo();
      return;
    }
    video.player.pause();
  }
  function startVideo(video) {
    if (window.innerWidth >= 768 && video.device === "desktop") {
      playVideo(video.player, video.type);
    }
    if (window.innerWidth < 768 && video.device === "mobile") {
      playVideo(video.player, video.type);
    }
    startButton == null ? void 0 : startButton.classList.add("hide");
    video.videoWrapper.classList.add(cssClasses.active);
  }
  function setEventListeners(videoContainer2, video) {
    videoContainer2.addEventListener("click", (event) => {
      if (event.target.closest(selectors2.startButton) || event.target.closest(selectors2.videoPlaceholder)) {
        startVideo(video);
      }
    });
    mobileSize.addEventListener("change", () => {
      if (video.type === "html") {
        if (video.device === "mobile" && !mobileSize.matches) {
          video.player.pause();
        }
        if (video.device === "desktop" && mobileSize.matches) {
          video.player.pause();
        }
      }
      if (video.type === "vimeo") {
        if (video.device === "mobile" && !mobileSize.matches) {
          video.player.pause();
        }
        if (video.device === "desktop" && mobileSize.matches) {
          video.player.pause();
        }
      }
      if (video.type === "youtube") {
        if (video.device === "mobile" && !mobileSize.matches) {
          video.player.pauseVideo();
        }
        if (video.device === "desktop" && mobileSize.matches) {
          video.player.pauseVideo();
        }
      }
      const section = video.videoWrapper.closest(selectors2.section);
      if (!section) {
        return;
      }
      const type = section.getAttribute(attributes2.type);
      if (type !== "popup") {
        return;
      }
      startVideo(video);
    });
  }
  async function init() {
    videos = initVideos(config);
    if (videos && videos.length) {
      videos.forEach((video) => {
        setEventListeners(videoContainer, video);
        const section = video.videoWrapper.closest(selectors2.section);
        if (!section) {
          return;
        }
        const sectionId = section.getAttribute(attributes2.sectionId);
        const type = section.getAttribute(attributes2.type);
        if (type !== "popup") {
          return;
        }
        window.themeCore.EventBus.listen(`Toggle:video-${sectionId}:open`, (target) => {
          if (!target.contains(video.videoWrapper) || getComputedStyle(video.videoWrapper).getPropertyValue("display") === "none") {
            return;
          }
          startVideo(video);
        });
        window.themeCore.EventBus.listen(`Toggle:video-${sectionId}:close`, (target) => {
          if (!target.contains(video.videoWrapper)) {
            return;
          }
          pauseVideo(video);
        });
      });
    }
  }
  return Object.freeze({
    init
  });
};
const selectors = {
  section: ".js-video-section",
  videoContainer: ".js-video-container",
  videoPopup: ".js-video-popup"
};
const attributes = {
  sectionId: "data-section-id"
};
const VideoSectionPlayer = () => {
  const Toggle = window.themeCore.utils.Toggle;
  let sections = [];
  let componentsList = {};
  function createComponents(Component, selector) {
    return sections.filter((section) => section.querySelector(selector)).map((section) => {
      const componentNode = section.querySelector(selector);
      const sectionId = section.getAttribute(attributes.sectionId);
      const videoPopup = section.querySelector(selectors.videoPopup);
      if (videoPopup) {
        const videoPopupToggle = Toggle({
          toggleSelector: `video-${sectionId}`
        });
        videoPopupToggle.init();
        videoPopup.addEventListener("click", (event) => {
          if (event.target === videoPopup) {
            videoPopupToggle.close(videoPopup);
          }
        });
      }
      return Component(componentNode);
    });
  }
  function init(sectionId) {
    sections = [...document.querySelectorAll(selectors.section)].filter((section) => !sectionId || section.closest(`#shopify-section-${sectionId}`));
    componentsList = {
      Video: createComponents(Video, selectors.videoContainer)
    };
    for (const list in componentsList) {
      componentsList[list].forEach((component) => component.init());
    }
  }
  return Object.freeze({
    init
  });
};
const action = () => {
  window.themeCore.VideoSectionPlayer = window.themeCore.VideoSectionPlayer || VideoSectionPlayer();
  window.themeCore.utils.register(window.themeCore.VideoSectionPlayer, "video");
};
if (window.themeCore && window.themeCore.loaded) {
  action();
} else {
  document.addEventListener("theme:all:loaded", action, { once: true });
}
