/**
 * MP3fy - Modern Spotify MP3 Downloader
 * Frontend JavaScript Controller with 100-Track Batching & Tailwind Glassmorphic UI
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  let currentPlaylist = null;
  let currentTasks = {}; // song_id -> task object
  let ws = null;
  let selectedSongIds = new Set();
  let activeBatchIndex = 0; // 0 = All tracks, 1 = Batch 1 (1-100), 2 = Batch 2 (101-200), etc.
  let appSettings = {
    output_dir: "~/Music",
    bitrate: "320",
  };

  // DOM Elements
  const htmlDoc = document.documentElement;
  const themeToggleBtn = document.getElementById("theme-toggle");
  const themeIcon = document.getElementById("theme-icon");
  const themeLabelText = document.getElementById("theme-label-text");

  const fetchForm = document.getElementById("fetch-form");
  const spotifyUrlInput = document.getElementById("spotify-url-input");
  const btnPaste = document.getElementById("btn-paste");
  const btnFetch = document.getElementById("btn-fetch");
  const btnFetchText = document.getElementById("btn-fetch-text");
  const btnFetchIcon = document.getElementById("btn-fetch-icon");
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

  // Batch Tabs Elements
  const batchTabsContainer = document.getElementById("batch-tabs-container");
  const batchTabsList = document.getElementById("batch-tabs-list");
  const btnDownloadActiveBatch = document.getElementById("btn-download-active-batch");
  const btnBatchDownloadText = document.getElementById("btn-batch-download-text");

  const btnDownloadAll = document.getElementById("btn-download-all");
  const btnCancelAll = document.getElementById("btn-cancel-all");
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
     1. THEME TOGGLE (Siyah / Beyaz Tema)
     ========================================== */
  function initTheme() {
    const savedTheme = localStorage.getItem("mp3fy_theme") || "dark";
    setTheme(savedTheme);
  }

  function setTheme(theme) {
    if (theme === "dark") {
      htmlDoc.classList.add("dark");
      htmlDoc.setAttribute("data-theme", "dark");
      if (themeIcon) themeIcon.textContent = "dark_mode";
      if (themeLabelText) themeLabelText.textContent = "Karanlık";
    } else {
      htmlDoc.classList.remove("dark");
      htmlDoc.setAttribute("data-theme", "light");
      if (themeIcon) themeIcon.textContent = "light_mode";
      if (themeLabelText) themeLabelText.textContent = "Aydınlık";
    }
    localStorage.setItem("mp3fy_theme", theme);
  }

  themeToggleBtn.addEventListener("click", () => {
    const isDark = htmlDoc.classList.contains("dark");
    const newTheme = isDark ? "light" : "dark";
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
      plDestFolder.textContent = data.output_dir;
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
        showToast(`Music klasörü açıldı: ${data.path}`, "success");
      } else {
        showToast("Klasör açılamadı.", "error");
      }
    } catch (e) {
      showToast("Klasör açılırken hata oluştu.", "error");
    }
  }

  btnHeaderOpenFolder.addEventListener("click", openMusicFolder);
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
        throw new Error(resData.detail || "Müzik bilgisi alınamadı.");
      }

      currentPlaylist = resData.data;
      activeBatchIndex = 0; // Default to all tracks or first batch
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
      if (btnFetchIcon) btnFetchIcon.classList.add("hidden");
      fetchSpinner.classList.remove("hidden");
    } else {
      btnFetch.disabled = false;
      btnFetchText.textContent = "Listeyi Getir";
      if (btnFetchIcon) btnFetchIcon.classList.remove("hidden");
      fetchSpinner.classList.add("hidden");
    }
  }

  /* ==========================================
     5. RENDER PLAYLIST & 100-TRACK BATCHES
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

    // Render Batch Selector Tabs (Yüzlük Bölümler)
    renderBatchTabs(playlist);

    // Reset selection to all tracks
    selectedSongIds = new Set(playlist.tracks.map((t) => t.id));
    selectAllCheckbox.checked = true;
    updateSelectionUI();

    // Render tracks table for active batch
    renderTracksTable();
    updateOverallProgress();
  }

  function renderBatchTabs(playlist) {
    batchTabsList.innerHTML = "";
    const batches = playlist.batches || [];

    if (batches.length <= 1) {
      // If 100 or fewer tracks, single batch mode
      btnDownloadActiveBatch.classList.add("hidden");
      const btnAll = document.createElement("button");
      btnAll.className = "bg-primary text-on-primary-fixed font-bold px-3 py-1 rounded-full text-xs font-label-sm shadow-md";
      btnAll.textContent = `Tüm Şarkılar (${playlist.tracks.length})`;
      btnAll.addEventListener("click", () => {
        activeBatchIndex = 0;
        setActiveBatchTab(btnAll);
        renderTracksTable();
      });
      batchTabsList.appendChild(btnAll);
      return;
    }

    btnDownloadActiveBatch.classList.remove("hidden");

    // "Tüm Şarkılar" Tab
    const btnAll = document.createElement("button");
    btnAll.className = `batch-pill-btn px-3 py-1 rounded-full text-xs font-label-sm transition-all border border-white/5 ${
      activeBatchIndex === 0
        ? "bg-primary text-on-primary-fixed font-bold shadow-md"
        : "bg-surface-container hover:bg-surface-container-high text-on-surface"
    }`;
    btnAll.textContent = `✨ Tümü (${playlist.tracks.length})`;
    btnAll.addEventListener("click", () => {
      activeBatchIndex = 0;
      setActiveBatchTab(btnAll);
      btnDownloadActiveBatch.classList.add("hidden");
      renderTracksTable();
    });
    batchTabsList.appendChild(btnAll);

    // 100-Track Batch Tabs
    batches.forEach((b) => {
      const btnBatch = document.createElement("button");
      btnBatch.className = `batch-pill-btn px-3 py-1 rounded-full text-xs font-label-sm transition-all border border-white/5 ${
        activeBatchIndex === b.batch_index
          ? "bg-primary text-on-primary-fixed font-bold shadow-md"
          : "bg-surface-container hover:bg-surface-container-high text-on-surface"
      }`;
      btnBatch.textContent = `📦 ${b.name}`;
      btnBatch.addEventListener("click", () => {
        activeBatchIndex = b.batch_index;
        setActiveBatchTab(btnBatch);
        btnDownloadActiveBatch.classList.remove("hidden");
        btnBatchDownloadText.textContent = `Bu Bölümü İndir (${b.count} Şarkı)`;
        renderTracksTable();
      });
      batchTabsList.appendChild(btnBatch);
    });

    if (activeBatchIndex > 0) {
      const currentB = batches.find((b) => b.batch_index === activeBatchIndex);
      if (currentB) {
        btnBatchDownloadText.textContent = `Bu Bölümü İndir (${currentB.count} Şarkı)`;
      }
    }
  }

  function setActiveBatchTab(activeButton) {
    document.querySelectorAll(".batch-pill-btn").forEach((btn) => {
      btn.className =
        "batch-pill-btn px-3 py-1 rounded-full text-xs font-label-sm transition-all border border-white/5 bg-surface-container hover:bg-surface-container-high text-on-surface";
    });
    activeButton.className =
      "batch-pill-btn px-3 py-1 rounded-full text-xs font-label-sm transition-all border border-white/5 bg-primary text-on-primary-fixed font-bold shadow-md";
  }

  function getVisibleTracks() {
    if (!currentPlaylist) return [];
    let tracks = currentPlaylist.tracks;

    // Filter by active batch
    if (activeBatchIndex > 0) {
      tracks = tracks.filter((t) => t.batch_index === activeBatchIndex);
    }

    // Filter by search text
    const filterVal = trackFilterInput.value.toLowerCase().trim();
    if (filterVal) {
      tracks = tracks.filter(
        (t) =>
          t.title.toLowerCase().includes(filterVal) ||
          t.artist.toLowerCase().includes(filterVal) ||
          t.album.toLowerCase().includes(filterVal)
      );
    }

    return tracks;
  }

  function renderTracksTable() {
    tracksTbody.innerHTML = "";
    const visibleTracks = getVisibleTracks();

    visibleTracks.forEach((track, index) => {
      const tr = document.createElement("tr");
      tr.id = `row-${track.id}`;
      tr.className = "hover:bg-surface-container-highest/30 transition-colors";
      tr.setAttribute("data-song-id", track.id);

      const isChecked = selectedSongIds.has(track.id);
      const task = currentTasks[track.id];
      const displayIndex = track.track_number || index + 1;

      tr.innerHTML = `
        <td class="py-3 px-4">
          <input type="checkbox" class="track-checkbox rounded border-white/20 bg-surface-container text-primary focus:ring-primary w-4 h-4 cursor-pointer" data-id="${track.id}" ${isChecked ? "checked" : ""}>
        </td>
        <td class="py-3 px-2 text-center text-on-surface-variant font-label-sm text-xs">${displayIndex}</td>
        <td class="py-3 px-4">
          <div class="flex items-center gap-3">
            <img src="${track.cover_url || "/static/img/placeholder.svg"}" alt="Thumb" class="w-10 h-10 rounded-lg object-cover flex-shrink-0 shadow-sm border border-white/5" />
            <div class="flex flex-col min-w-0">
              <span class="font-bold text-on-surface truncate max-w-xs md:max-w-md text-sm" title="${escapeHtml(track.title)}">${escapeHtml(track.title)}</span>
              <span class="text-on-surface-variant text-xs truncate max-w-xs md:max-w-md" title="${escapeHtml(track.artist)}">${escapeHtml(track.artist)}</span>
            </div>
          </div>
        </td>
        <td class="py-3 px-4 text-on-surface-variant text-xs hidden md:table-cell truncate max-w-[180px]" title="${escapeHtml(track.album || "-")}">${escapeHtml(track.album || "-")}</td>
        <td class="py-3 px-4 text-center text-on-surface-variant font-label-sm text-xs">${track.duration_formatted}</td>
        <td class="py-3 px-4">
          <div id="status-container-${track.id}">
            ${renderStatusBadge(task)}
          </div>
        </td>
        <td class="py-3 px-4 text-right">
          <div class="flex items-center justify-end gap-1">
            ${
              track.preview_url || (task && task.status === "completed")
                ? `<button class="p-1.5 hover:bg-surface-container rounded-lg text-primary transition-colors btn-play" data-id="${track.id}" title="Dinle / Önizle">
                     <span class="material-symbols-outlined text-sm">play_arrow</span>
                   </button>`
                : ""
            }
            <button class="bg-surface-container hover:bg-surface-container-high text-on-surface px-2.5 py-1 rounded-lg text-xs font-label-sm font-semibold transition-colors flex items-center gap-1 btn-download-single border border-white/5" data-id="${track.id}" title="Bu Şarkıyı İndir">
              <span class="material-symbols-outlined text-xs">download</span>
              <span>İndir</span>
            </button>
          </div>
        </td>
      `;

      tracksTbody.appendChild(tr);
    });

    attachTrackRowEvents();
    updateSelectionUI();
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
      return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-label-sm font-medium bg-surface-container-highest/60 text-on-surface-variant"><span class="w-1.5 h-1.5 rounded-full bg-on-surface-variant/40"></span> Hazır</span>`;
    }

    const s = task.status;
    if (s === "queued") {
      return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-label-sm font-medium bg-surface-container text-on-surface-variant"><span class="material-symbols-outlined text-[12px] animate-pulse">schedule</span> Kuyrukta</span>`;
    } else if (s === "searching") {
      return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-label-sm font-medium bg-info/20 text-info"><span class="material-symbols-outlined text-[12px] animate-spin">sync</span> Aranıyor...</span>`;
    } else if (s === "downloading") {
      return `
        <div class="flex flex-col gap-1 w-full max-w-[130px]">
          <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-label-sm font-bold bg-warning/20 text-warning">
            <span class="material-symbols-outlined text-[11px] animate-bounce">download</span> %${task.progress.toFixed(0)} (${task.speed || "..."})
          </span>
          <div class="w-full h-1 bg-surface-container-highest rounded-full overflow-hidden">
            <div class="h-full bg-warning rounded-full transition-all duration-200" style="width: ${task.progress}%;"></div>
          </div>
        </div>
      `;
    } else if (s === "converting") {
      return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-label-sm font-medium bg-primary/20 text-primary"><span class="material-symbols-outlined text-[12px] animate-spin">settings</span> MP3 İşleniyor</span>`;
    } else if (s === "tagging") {
      return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-label-sm font-medium bg-cyan-500/20 text-cyan-400"><span class="material-symbols-outlined text-[12px]">label</span> Etiketleniyor</span>`;
    } else if (s === "completed") {
      return `
        <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-label-sm font-bold bg-green-500/20 text-green-400">
          <span class="material-symbols-outlined text-[12px]">check_circle</span> Tamamlandı ${task.file_size_mb ? `(${task.file_size_mb} MB)` : ""}
        </span>
      `;
    } else if (s === "error") {
      return `
        <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-label-sm font-bold bg-error/20 text-error" title="${escapeHtml(task.error_message || "Hata")}">
          <span class="material-symbols-outlined text-[12px]">error</span> Hata
        </span>
      `;
    } else if (s === "cancelled") {
      return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-label-sm bg-surface-container text-on-surface-variant"><span class="material-symbols-outlined text-[12px]">block</span> İptal</span>`;
    }

    return `<span class="px-2 py-0.5 rounded text-xs bg-surface-container text-on-surface">${s}</span>`;
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
    const visible = getVisibleTracks();
    if (e.target.checked) {
      visible.forEach((t) => selectedSongIds.add(t.id));
    } else {
      visible.forEach((t) => selectedSongIds.delete(t.id));
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

    const visible = getVisibleTracks();
    if (visible.length > 0) {
      const allVisibleSelected = visible.every((t) => selectedSongIds.has(t.id));
      selectAllCheckbox.checked = allVisibleSelected;
    }
  }

  trackFilterInput.addEventListener("input", () => {
    if (currentPlaylist) {
      renderTracksTable();
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

  btnDownloadActiveBatch.addEventListener("click", async () => {
    if (!currentPlaylist) return;
    const batchTracks = currentPlaylist.tracks.filter(
      (t) => activeBatchIndex === 0 || t.batch_index === activeBatchIndex
    );
    const toDownload = batchTracks.filter((t) => selectedSongIds.has(t.id));

    if (toDownload.length === 0) {
      showToast("Bu bölümde seçili şarkı yok.", "error");
      return;
    }

    showToast(`Bölümdeki ${toDownload.length} şarkı indirme kuyruğuna alındı.`, "success");
    btnCancelAll.classList.remove("hidden");

    try {
      const res = await fetch("/api/download/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ songs: toDownload }),
      });
      const data = await res.json();
      if (res.ok && data.tasks) {
        data.tasks.forEach((t) => {
          currentTasks[t.id] = t;
          updateTrackRow(t);
        });
      }
    } catch (e) {
      showToast("Bölüm indirmesi başlatılamadı.", "error");
    }
  });

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
    toast.className = `glass-panel px-4 py-3 rounded-xl shadow-xl flex items-center gap-2 text-xs font-label-md font-semibold border transition-all animate-bounce ${
      type === "success"
        ? "border-green-500/30 text-green-400"
        : type === "error"
        ? "border-error/30 text-error"
        : "border-primary/30 text-primary"
    }`;

    let icon = "info";
    if (type === "success") icon = "check_circle";
    if (type === "error") icon = "error";

    toast.innerHTML = `
      <span class="material-symbols-outlined text-sm">${icon}</span>
      <span>${escapeHtml(message)}</span>
    `;

    toastContainer.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
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
