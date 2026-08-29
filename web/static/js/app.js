/**
 * MP3fy - Modern Spotify MP3 Downloader
 * Frontend JavaScript Controller
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  let currentPlaylist = null;
  let currentTasks = {}; // song_id -> task object
  let ws = null;
  let selectedSongIds = new Set();
  let appSettings = {
    output_dir: "music/",
    bitrate: "320",
  };

  // DOM Elements
  const htmlDoc = document.documentElement;
  const themeToggleBtn = document.getElementById("theme-toggle");
  const themeLabelText = document.getElementById("theme-label-text");

  const fetchForm = document.getElementById("fetch-form");
  const spotifyUrlInput = document.getElementById("spotify-url-input");
  const btnPaste = document.getElementById("btn-paste");
  const btnFetch = document.getElementById("btn-fetch");
  const btnFetchText = document.getElementById("btn-fetch-text");
  const fetchSpinner = document.getElementById("fetch-spinner");
  const sampleChips = document.querySelectorAll(".sample-chip");

  const playlistSection = document.getElementById("playlist-section");
  const emptyState = document.getElementById("empty-state");
  const plCover = document.getElementById("pl-cover");
  const plBadge = document.getElementById("pl-badge");
  const plTypeLabel = document.getElementById("pl-type-label");
  const plTitle = document.getElementById("pl-title");
  const plDesc = document.getElementById("pl-desc");
  const plOwner = document.getElementById("pl-owner");
  const plTrackCount = document.getElementById("pl-track-count");
  const plTotalDuration = document.getElementById("pl-total-duration");
  const plDestFolder = document.getElementById("pl-dest-folder");

  const btnDownloadAll = document.getElementById("btn-download-all");
  const btnCancelAll = document.getElementById("btn-cancel-all");
  const btnOpenMusicFolder = document.getElementById("btn-open-music-folder");
  const btnHeaderOpenFolder = document.getElementById("btn-open-folder");
  const selectedCountLabel = document.getElementById("selected-count-label");

  const overallProgressBar = document.getElementById("overall-progress-bar");
  const overallPercentText = document.getElementById("overall-percent-text");
  const overallStatsText = document.getElementById("overall-stats-text");

  const selectAllCheckbox = document.getElementById("select-all-checkbox");
  const selectedBadge = document.getElementById("selected-badge");
  const trackFilterInput = document.getElementById("track-filter-input");
  const tracksTbody = document.getElementById("tracks-tbody");

  // Settings Modal Elements
  const settingsModal = document.getElementById("settings-modal");
  const btnSettingsOpen = document.getElementById("btn-settings-open");
  const btnCloseSettings = document.getElementById("btn-close-settings");
  const btnCancelSettings = document.getElementById("btn-cancel-settings");
  const btnSaveSettings = document.getElementById("btn-save-settings");
  const settingOutputDir = document.getElementById("setting-output-dir");
  const settingBitrate = document.getElementById("setting-bitrate");
  const settingClientId = document.getElementById("setting-client-id");
  const settingClientSecret = document.getElementById("setting-client-secret");
  const btnOpenDirSettings = document.getElementById("btn-open-dir-settings");

  // Floating Player Elements
  const floatingPlayer = document.getElementById("floating-player");
  const playerThumb = document.getElementById("player-thumb");
  const playerTitle = document.getElementById("player-title");
  const playerArtist = document.getElementById("player-artist");
  const nativeAudio = document.getElementById("native-audio");
  const playerClose = document.getElementById("player-close");

  // Toast Container
  const toastContainer = document.getElementById("toast-container");

  /* ==========================================
     1. THEME TOGGLE (Siyah / Beyaz Tema Düğmesi)
     ========================================== */
  function initTheme() {
    const savedTheme = localStorage.getItem("mp3fy_theme") || "dark";
    setTheme(savedTheme);
  }

  function setTheme(theme) {
    htmlDoc.setAttribute("data-theme", theme);
    localStorage.setItem("mp3fy_theme", theme);
    if (theme === "dark") {
      themeLabelText.textContent = "Karanlık";
    } else {
      themeLabelText.textContent = "Aydınlık";
    }
  }

  themeToggleBtn.addEventListener("click", () => {
    const currentTheme = htmlDoc.getAttribute("data-theme") || "dark";
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    setTheme(newTheme);
    showToast(
      newTheme === "dark" ? "Karanlık tema etkinleştirildi." : "Aydınlık tema etkinleştirildi.",
      "info"
    );
  });

  /* ==========================================
     2. WEBSOCKET CONNECTION
     ========================================== */
  function initWebSocket() {
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${location.host}/ws`;

    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("WebSocket connection established");
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === "init") {
          currentTasks = msg.tasks || {};
          updateAllTrackRows();
          updateOverallProgress();
        } else if (msg.type === "task_update") {
          const task = msg.task;
          currentTasks[task.id] = task;
          updateTrackRow(task);
          updateOverallProgress();
        }
      } catch (e) {
        console.error("Error parsing WS message:", e);
      }
    };

    ws.onclose = () => {
      console.log("WebSocket closed, attempting reconnect in 3s...");
      setTimeout(initWebSocket, 3000);
    };

    ws.onerror = (err) => {
      console.error("WebSocket error:", err);
    };
  }

  /* ==========================================
     3. SETTINGS & FOLDER ACTIONS
     ========================================== */
  async function loadSettings() {
    try {
      const res = await fetch("/api/settings");
      const data = await res.json();
      appSettings = data;
      settingOutputDir.value = data.output_dir;
      settingBitrate.value = data.bitrate;
      if (data.spotify_client_id) settingClientId.value = data.spotify_client_id;
      plDestFolder.textContent = data.output_dir.endsWith("/") ? data.output_dir : data.output_dir + "/";
    } catch (e) {
      console.error("Error loading settings:", e);
    }
  }

  btnSettingsOpen.addEventListener("click", () => {
    loadSettings();
    settingsModal.classList.remove("hidden");
  });

  function closeSettingsModal() {
    settingsModal.classList.add("hidden");
  }

  btnCloseSettings.addEventListener("click", closeSettingsModal);
  btnCancelSettings.addEventListener("click", closeSettingsModal);

  btnSaveSettings.addEventListener("click", async () => {
    try {
      const payload = {
        output_dir: settingOutputDir.value.trim(),
        bitrate: settingBitrate.value,
        spotify_client_id: settingClientId.value.trim(),
        spotify_client_secret: settingClientSecret.value.trim(),
      };
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (res.ok) {
        showToast("Ayarlar başarıyla kaydedildi!", "success");
        closeSettingsModal();
        loadSettings();
      } else {
        showToast(data.detail || "Ayarlar kaydedilemedi.", "error");
      }
    } catch (e) {
      showToast("Ayarlar kaydedilirken hata oluştu.", "error");
    }
  });

  async function openMusicFolder() {
    try {
      const res = await fetch("/api/open-folder", { method: "POST" });
      const data = await res.json();
      if (data.status === "success") {
        showToast(`Klasör açıldı: ${data.path}`, "success");
      } else {
        showToast("Klasör açılamadı. Dizin oluşturulmamış olabilir.", "error");
      }
    } catch (e) {
      showToast("Klasör açılırken hata oluştu.", "error");
    }
  }

  btnHeaderOpenFolder.addEventListener("click", openMusicFolder);
  btnOpenMusicFolder.addEventListener("click", openMusicFolder);
  btnOpenDirSettings.addEventListener("click", openMusicFolder);

  /* ==========================================
     4. URL INPUT & FETCHING
     ========================================== */
  btnPaste.addEventListener("click", async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        spotifyUrlInput.value = text.trim();
        showToast("Panodan yapıştırıldı!", "info");
      }
    } catch (err) {
      showToast("Pano okuma izni verilmedi.", "error");
    }
  });

  sampleChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      const url = chip.getAttribute("data-url");
      spotifyUrlInput.value = url;
      fetchPlaylist(url);
    });
  });

  fetchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const url = spotifyUrlInput.value.trim();
    if (url) {
      fetchPlaylist(url);
    }
  });

  async function fetchPlaylist(url) {
    setLoadingState(true);
    try {
      const res = await fetch("/api/fetch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });
      const resData = await res.json();

      if (!res.ok) {
        throw new Error(resData.detail || "Çalma listesi bilgisi alınamadı.");
      }

      currentPlaylist = resData.data;
      renderPlaylist(currentPlaylist);
      showToast(`${currentPlaylist.tracks.length} şarkı başarıyla getirildi!`, "success");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoadingState(false);
    }
  }

  function setLoadingState(isLoading) {
    if (isLoading) {
      btnFetch.disabled = true;
      btnFetchText.textContent = "Getiriliyor...";
      fetchSpinner.classList.remove("hidden");
    } else {
      btnFetch.disabled = false;
      btnFetchText.textContent = "Listeyi Getir";
      fetchSpinner.classList.add("hidden");
    }
  }

  /* ==========================================
     5. RENDER PLAYLIST & TRACKS
     ========================================== */
  function renderPlaylist(playlist) {
    emptyState.classList.add("hidden");
    playlistSection.classList.remove("hidden");

    // Header info
    plCover.src = playlist.cover_url || "/static/img/placeholder.svg";
    plBadge.textContent = playlist.type.toUpperCase();
    plTypeLabel.textContent = `SPOTIFY ${playlist.type.toUpperCase()}`;
    plTitle.textContent = playlist.title;
    plDesc.textContent = playlist.description || "Spotify üzerinden getirildi.";
    plOwner.textContent = playlist.owner;
    plTrackCount.textContent = playlist.total_tracks;

    // Calculate total duration
    let totalMs = 0;
    playlist.tracks.forEach((t) => (totalMs += t.duration_ms || 0));
    plTotalDuration.textContent = formatDuration(totalMs);

    // Reset selection to all tracks
    selectedSongIds = new Set(playlist.tracks.map((t) => t.id));
    selectAllCheckbox.checked = true;
    updateSelectionUI();

    // Render table
    renderTracksTable(playlist.tracks);
    updateOverallProgress();
  }

  function renderTracksTable(tracks) {
    tracksTbody.innerHTML = "";
    const filterVal = trackFilterInput.value.toLowerCase().trim();

    tracks.forEach((track, index) => {
      if (
        filterVal &&
        !track.title.toLowerCase().includes(filterVal) &&
        !track.artist.toLowerCase().includes(filterVal) &&
        !track.album.toLowerCase().includes(filterVal)
      ) {
        return; // Filtered out
      }

      const tr = document.createElement("tr");
      tr.id = `row-${track.id}`;
      tr.setAttribute("data-song-id", track.id);

      const isChecked = selectedSongIds.has(track.id);
      const task = currentTasks[track.id];

      tr.innerHTML = `
        <td>
          <label class="custom-checkbox-wrapper">
            <input type="checkbox" class="track-checkbox" data-id="${track.id}" ${isChecked ? "checked" : ""}>
            <span class="checkbox-custom"></span>
          </label>
        </td>
        <td class="track-index">${index + 1}</td>
        <td>
          <div class="track-main-cell">
            <img src="${track.cover_url || "/static/img/placeholder.svg"}" alt="Thumb" class="track-thumb" />
            <div class="track-meta">
              <span class="track-name" title="${track.title}">${escapeHtml(track.title)}</span>
              <span class="track-artist" title="${track.artist}">${escapeHtml(track.artist)}</span>
            </div>
          </div>
        </td>
        <td class="track-album" title="${track.album}">${escapeHtml(track.album || "-")}</td>
        <td class="track-duration">${track.duration_formatted}</td>
        <td>
          <div class="status-badge-container" id="status-container-${track.id}">
            ${renderStatusBadge(task)}
          </div>
        </td>
        <td>
          <div class="track-actions">
            ${
              track.preview_url || (task && task.status === "completed")
                ? `<button class="btn btn-icon btn-sm btn-play" data-id="${track.id}" title="Önizle / Dinle">
                     <i class="fa-solid fa-play"></i>
                   </button>`
                : ""
            }
            <button class="btn btn-secondary btn-sm btn-download-single" data-id="${track.id}" title="Bu Şarkıyı İndir">
              <i class="fa-solid fa-download"></i>
              <span>İndir</span>
            </button>
          </div>
        </td>
      `;

      tracksTbody.appendChild(tr);
    });

    attachTrackRowEvents();
  }

  function attachTrackRowEvents() {
    // Checkbox toggles
    document.querySelectorAll(".track-checkbox").forEach((cb) => {
      cb.addEventListener("change", (e) => {
        const id = e.target.getAttribute("data-id");
        if (e.target.checked) {
          selectedSongIds.add(id);
        } else {
          selectedSongIds.delete(id);
        }
        updateSelectionUI();
      });
    });

    // Single Download buttons
    document.querySelectorAll(".btn-download-single").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-id");
        const song = currentPlaylist.tracks.find((t) => t.id === id);
        if (song) {
          downloadSingleSong(song);
        }
      });
    });

    // Play buttons
    document.querySelectorAll(".btn-play").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-id");
        const song = currentPlaylist.tracks.find((t) => t.id === id);
        const task = currentTasks[id];
        if (song) {
          playAudioPreview(song, task);
        }
      });
    });
  }

  function renderStatusBadge(task) {
    if (!task) {
      return `<span class="status-badge status-queued"><i class="fa-regular fa-circle"></i> Hazır</span>`;
    }

    const s = task.status;
    if (s === "queued") {
      return `<span class="status-badge status-queued"><i class="fa-solid fa-clock"></i> Kuyrukta</span>`;
    } else if (s === "searching") {
      return `<span class="status-badge status-searching"><i class="fa-solid fa-magnifying-glass fa-spin"></i> Aranıyor...</span>`;
    } else if (s === "downloading") {
      return `
        <span class="status-badge status-downloading">
          <i class="fa-solid fa-arrow-down fa-bounce"></i> %${task.progress.toFixed(0)} (${task.speed || "..."})
        </span>
        <div class="mini-progress-bar">
          <div class="mini-progress-fill" style="width: ${task.progress}%;"></div>
        </div>
      `;
    } else if (s === "converting") {
      return `<span class="status-badge status-converting"><i class="fa-solid fa-gear fa-spin"></i> MP3 Dönüştürülüyor</span>`;
    } else if (s === "tagging") {
      return `<span class="status-badge status-tagging"><i class="fa-solid fa-tag fa-beat"></i> Etiketler Yazılıyor</span>`;
    } else if (s === "completed") {
      return `
        <span class="status-badge status-completed">
          <i class="fa-solid fa-circle-check"></i> Tamamlandı ${task.file_size_mb ? `(${task.file_size_mb} MB)` : ""}
        </span>
      `;
    } else if (s === "error") {
      return `
        <span class="status-badge status-error" title="${escapeHtml(task.error_message || "Hata")}">
          <i class="fa-solid fa-circle-xmark"></i> Hata
        </span>
      `;
    } else if (s === "cancelled") {
      return `<span class="status-badge status-cancelled"><i class="fa-solid fa-ban"></i> İptal Edildi</span>`;
    }

    return `<span class="status-badge status-queued">${s}</span>`;
  }

  function updateTrackRow(task) {
    const container = document.getElementById(`status-container-${task.id}`);
    if (container) {
      container.innerHTML = renderStatusBadge(task);
    }
  }

  function updateAllTrackRows() {
    if (!currentPlaylist) return;
    currentPlaylist.tracks.forEach((track) => {
      const task = currentTasks[track.id];
      updateTrackRow(task || { id: track.id, status: "ready" });
    });
  }

  /* ==========================================
     6. SELECTION & FILTERING
     ========================================== */
  selectAllCheckbox.addEventListener("change", (e) => {
    if (!currentPlaylist) return;
    if (e.target.checked) {
      selectedSongIds = new Set(currentPlaylist.tracks.map((t) => t.id));
    } else {
      selectedSongIds.clear();
    }
    document.querySelectorAll(".track-checkbox").forEach((cb) => {
      cb.checked = e.target.checked;
    });
    updateSelectionUI();
  });

  function updateSelectionUI() {
    const count = selectedSongIds.size;
    selectedCountLabel.textContent = count;
    selectedBadge.textContent = `${count} seçili`;
    btnDownloadAll.disabled = count === 0;
    if (currentPlaylist) {
      selectAllCheckbox.checked = count === currentPlaylist.tracks.length;
    }
  }

  trackFilterInput.addEventListener("input", () => {
    if (currentPlaylist) {
      renderTracksTable(currentPlaylist.tracks);
    }
  });

  /* ==========================================
     7. DOWNLOAD DISPATCH
     ========================================== */
  async function downloadSingleSong(song) {
    try {
      showToast(`"${song.title}" indirme kuyruğuna alındı.`, "info");
      const res = await fetch("/api/download/single", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ song }),
      });
      const data = await res.json();
      if (res.ok) {
        currentTasks[song.id] = data.task;
        updateTrackRow(data.task);
      }
    } catch (e) {
      showToast("İndirme başlatılamadı.", "error");
    }
  }

  btnDownloadAll.addEventListener("click", async () => {
    if (!currentPlaylist || selectedSongIds.size === 0) return;

    const songsToDownload = currentPlaylist.tracks.filter((t) => selectedSongIds.has(t.id));
    showToast(`${songsToDownload.length} şarkı indirme kuyruğuna eklendi.`, "success");

    btnCancelAll.classList.remove("hidden");

    try {
      const res = await fetch("/api/download/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ songs: songsToDownload }),
      });
      const data = await res.json();
      if (res.ok && data.tasks) {
        data.tasks.forEach((t) => {
          currentTasks[t.id] = t;
          updateTrackRow(t);
        });
      }
    } catch (e) {
      showToast("Toplu indirme başlatılırken hata oluştu.", "error");
    }
  });

  btnCancelAll.addEventListener("click", async () => {
    try {
      await fetch("/api/cancel-all", { method: "POST" });
      showToast("İndirmeler durduruldu.", "info");
      btnCancelAll.classList.add("hidden");
    } catch (e) {
      showToast("İptal işlemi başarısız oldu.", "error");
    }
  });

  function updateOverallProgress() {
    if (!currentPlaylist || currentPlaylist.tracks.length === 0) return;

    const total = currentPlaylist.tracks.length;
    let completed = 0;
    let inProgress = 0;

    currentPlaylist.tracks.forEach((t) => {
      const task = currentTasks[t.id];
      if (task && task.status === "completed") {
        completed++;
      } else if (
        task &&
        ["searching", "downloading", "converting", "tagging"].includes(task.status)
      ) {
        inProgress++;
      }
    });

    const percent = Math.round((completed / total) * 100);
    overallProgressBar.style.width = `${percent}%`;
    overallPercentText.textContent = `${percent}%`;
    overallStatsText.textContent = `${completed} / ${total} Tamamlandı ${inProgress > 0 ? `(${inProgress} İndiriliyor)` : ""}`;

    if (inProgress === 0 && completed > 0) {
      btnCancelAll.classList.add("hidden");
    }
  }

  /* ==========================================
     8. FLOATING AUDIO PLAYER
     ========================================== */
  function playAudioPreview(song, task) {
    let audioSrc = "";
    if (task && task.status === "completed" && task.file_path) {
      audioSrc = `/api/music/file?path=${encodeURIComponent(task.file_path)}`;
    } else if (song.preview_url) {
      audioSrc = song.preview_url;
    }

    if (!audioSrc) {
      showToast("Bu şarkı için ses önizlemesi bulunamadı.", "error");
      return;
    }

    playerThumb.src = song.cover_url || "/static/img/placeholder.svg";
    playerTitle.textContent = song.title;
    playerArtist.textContent = song.artist;
    nativeAudio.src = audioSrc;
    nativeAudio.play().catch((e) => console.log("Autoplay blocked:", e));

    floatingPlayer.classList.remove("hidden");
  }

  playerClose.addEventListener("click", () => {
    nativeAudio.pause();
    nativeAudio.src = "";
    floatingPlayer.classList.add("hidden");
  });

  /* ==========================================
     9. TOAST NOTIFICATIONS
     ========================================== */
  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    let icon = "fa-solid fa-circle-info";
    if (type === "success") icon = "fa-solid fa-circle-check";
    if (type === "error") icon = "fa-solid fa-circle-exclamation";

    toast.innerHTML = `
      <i class="${icon}"></i>
      <span>${escapeHtml(message)}</span>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.animation = "slideInRight 0.3s ease reverse";
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  /* ==========================================
     10. HELPERS
     ========================================== */
  function formatDuration(ms) {
    if (!ms || ms <= 0) return "0:00";
    const totalSec = Math.floor(ms / 1000);
    const hrs = Math.floor(totalSec / 3600);
    const mins = Math.floor((totalSec % 3600) / 60);
    const secs = totalSec % 60;
    if (hrs > 0) {
      return `${hrs} sa ${mins} dk`;
    }
    return `${mins} dk ${secs} sn`;
  }

  function escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  // Initialization
  initTheme();
  initWebSocket();
  loadSettings();
});
