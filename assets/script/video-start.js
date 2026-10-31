(function () {
  "use strict";

  document.querySelectorAll("video[data-start-time]").forEach((video) => {
    if (video.dataset.startTimeBound) return;

    const startTime = Number(video.dataset.startTime);
    if (!Number.isFinite(startTime) || startTime < 0) return;
    video.dataset.startTimeBound = "true";

    const enforceStart = () => {
      if (video.readyState < 1) return;

      // An out-of-range start leaves no playable interval. Do not silently
      // fall back to showing content before the configured boundary.
      if (Number.isFinite(video.duration) && startTime >= video.duration) {
        video.pause();
        video.controls = false;
        return;
      }

      // The media fragment sets the initial position; this guard also covers
      // backward scrubbing, keyboard seeks, and replay after the video ends.
      // Keep valid positions untouched so pause/resume continues normally.
      if (video.currentTime < startTime) video.currentTime = startTime;
    };

    ["loadedmetadata", "durationchange", "loadeddata", "seeking", "seeked",
      "play", "playing", "timeupdate"].forEach((event) => {
      video.addEventListener(event, enforceStart);
    });
    enforceStart();
  });
}());
