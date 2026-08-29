/**
 * MP3fy - Modern Spotify MP3 Downloader
 * Frontend JavaScript Controller with Bilingual (TR/EN) Support, 100-Track Batching & Folder Selection
 */

document.addEventListener("DOMContentLoaded", () => {
  // State
  let currentPlaylist = null;
  let currentTasks = {}; // song_id -> task object
  let ws = null;
  let selectedSongIds = new Set();
  let activeBatchIndex = 0; // 0 = All tracks, 1 = Batch 1, 2 = Batch 2, etc.
  let currentLang = localStorage.getItem("mp3fy_lang") || "tr";
  let appSettings = {
    output_dir: "~/Music",
    bitrate: "320",
  };

  /* ==========================================
     TRANSLATION DICTIONARY (TR / EN)
     ========================================== */
  const i18n = {
    tr: {
      langBadge: "TR",
      themeDark: "Karanlık",
      themeLight: "Aydınlık",
      folderPrefix: "Klasör",
      navFolderTitle: "İndirilecek klasörü seç veya değiştir",
      openFolderTitle: "Seçili indirme klasörünü aç",
      themeTitle: "Temayı Değiştir",
      langTitle: "Dili Değiştir (Türkçe / English)",
      heroTitle: "Listenizin gerçek sahibi olun!",
      urlPlaceholder: "Spotify Çalma Listesi, Albüm veya Şarkı linki yapıştırın...",
      btnPaste: "Yapıştır",
      btnFetch: "Listeyi Getir",
      btnFetching: "Getiriliyor...",
      sampleLinks: "Örnek Linkler:",
      emptyTitle: "Henüz bir liste getirilmedi",
      emptyDesc: "Yukarıdaki arama çubuğuna Spotify linkinizi yapıştırın ve \"Listeyi Getir\" butonuna basın.",
      playlistBadge: "PLAYLIST",
      albumBadge: "ALBÜM",
      trackBadge: "ŞARKI",
      typePlaylist: "SPOTIFY ÇALMA LİSTESİ",
      typeAlbum: "SPOTIFY ALBÜMÜ",
      typeTrack: "SPOTIFY TEKİL ŞARKI",
      tracksCountLabel: "Şarkı",
      changeFolderTooltip: "İndirme klasörünü değiştir",
      btnDownloadAll: "Tümünü İndir",
      btnDownloadBatch: "Bu Bölümü İndir",
      btnCancelAll: "Durdur",
      batchLabel: "Bölümler:",
      batchAll: "Tüm Şarkılar",
      batchPrefix: "Bölüm",
      filterPlaceholder: "Filtrele...",
      progressLabel: "İlerleme Durumu",
      completedStats: "{completed} / {total} Tamamlandı",
      downloadingStats: "({count} İndiriliyor)",
      selectVisible: "Görünenleri Seç",
      selectedBadge: "{count} seçili",
      thTrack: "Şarkı & Sanatçı",
      thAlbum: "Albüm",
      thStatus: "Durum",
      thAction: "İşlem",
      btnDownloadSingle: "İndir",
      btnPreview: "Dinle / Önizle",
      // Statuses
      statusReady: "Hazır",
      statusQueued: "Kuyrukta",
      statusSearching: "Aranıyor...",
      statusDownloading: "İndiriliyor",
      statusConverting: "MP3 İşleniyor",
      statusTagging: "Etiketleniyor",
      statusCompleted: "Tamamlandı",
      statusError: "Hata",
      statusCancelled: "İptal",
      // Folder Modal
      folderModalTitle: "İndirme Klasörünü Seçin",
      currentFolderLabel: "Mevcut İndirme Konumu:",
      btnOpenFolderModal: "Aç",
      btnBrowseNative: "Bilgisayardan Klasör Seç (Gözat...)",
      btnBrowsingNative: "Klasör Seçiliyor...",
      quickLocations: "Hızlı Konumlar:",
      customPathLabel: "veya Özel Dizin Yolu Yazın:",
      btnApplyPath: "Uygula",
      btnDone: "Tamam",
      // Settings Modal
      settingsTitle: "Uygulama Ayarları",
      settingDirLabel: "İndirme Klasörü (Hedef Dizin):",
      settingDirDesc: "Varsayılan olarak kullanıcının ev dizinindeki ~/Music klasörüne kaydedilir.",
      settingQualityLabel: "MP3 Ses Kalitesi:",
      settingApiLabel: "Spotify API Anahtarları (İsteğe Bağlı):",
      settingApiDesc: "Standart indirmelerde API anahtarına gerek yoktur.",
      btnCancel: "İptal",
      btnSave: "Kaydet",
      // Toasts
      toastCopied: "Panodan yapıştırıldı!",
      toastNoClipboard: "Pano okuma izni verilmedi.",
      toastFetched: "{count} şarkı başarıyla getirildi!",
      toastBatchQueued: "Bölümdeki {count} şarkı indirme kuyruğuna alındı.",
      toastAllQueued: "{count} şarkı indirme kuyruğuna alındı.",
      toastSingleQueued: '"{title}" indirme kuyruğuna alındı.',
      toastCancelled: "İndirmeler durduruldu.",
      toastFolderSet: "İndirme konumu ayarlandı: {path}",
      toastFolderOpened: "Klasör açıldı: {path}",
      toastFolderError: "Klasör açılamadı.",
      toastSettingsSaved: "Ayarlar başarıyla kaydedildi!",
      toastThemeDark: "Karanlık tema etkinleştirildi.",
      toastThemeLight: "Aydınlık tema etkinleştirildi.",
      toastLangSwitched: "Dil Türkçe olarak ayarlandı.",
    },
    en: {
      langBadge: "EN",
      themeDark: "Dark",
      themeLight: "Light",
      folderPrefix: "Folder",
      navFolderTitle: "Select or change download folder",
      openFolderTitle: "Open selected download folder",
      themeTitle: "Toggle Theme",
      langTitle: "Change Language (English / Türkçe)",
      heroTitle: "Own your music, for real!",
      urlPlaceholder: "Paste Spotify Playlist, Album or Track link...",
      btnPaste: "Paste",
      btnFetch: "Fetch Playlist",
      btnFetching: "Fetching...",
      sampleLinks: "Sample Links:",
      emptyTitle: "No playlist fetched yet",
      emptyDesc: "Paste your Spotify link in the search bar above and click \"Fetch Playlist\".",
      playlistBadge: "PLAYLIST",
      albumBadge: "ALBUM",
      trackBadge: "TRACK",
      typePlaylist: "SPOTIFY PLAYLIST",
      typeAlbum: "SPOTIFY ALBUM",
      typeTrack: "SPOTIFY SINGLE TRACK",
      tracksCountLabel: "Tracks",
      changeFolderTooltip: "Change download folder",
      btnDownloadAll: "Download All",
      btnDownloadBatch: "Download Batch",
      btnCancelAll: "Cancel All",
      batchLabel: "Batches:",
      batchAll: "All Tracks",
      batchPrefix: "Batch",
      filterPlaceholder: "Filter...",
      progressLabel: "Overall Progress",
      completedStats: "{completed} / {total} Completed",
      downloadingStats: "({count} Downloading)",
      selectVisible: "Select Visible",
      selectedBadge: "{count} selected",
      thTrack: "Track & Artist",
      thAlbum: "Album",
      thStatus: "Status",
      thAction: "Action",
      btnDownloadSingle: "Download",
      btnPreview: "Preview / Play",
      // Statuses
      statusReady: "Ready",
      statusQueued: "Queued",
      statusSearching: "Searching...",
      statusDownloading: "Downloading",
      statusConverting: "Converting MP3",
      statusTagging: "Tagging ID3",
      statusCompleted: "Completed",
      statusError: "Error",
      statusCancelled: "Cancelled",
      // Folder Modal
      folderModalTitle: "Select Download Folder",
      currentFolderLabel: "Current Download Location:",
      btnOpenFolderModal: "Open",
      btnBrowseNative: "Browse Computer Folder...",
      btnBrowsingNative: "Browsing Folder...",
      quickLocations: "Quick Locations:",
      customPathLabel: "or Enter Custom Path:",
      btnApplyPath: "Apply",
      btnDone: "Done",
      // Settings Modal
      settingsTitle: "App Settings",
      settingDirLabel: "Download Folder (Target Directory):",
      settingDirDesc: "By default, files are saved to ~/Music in your home folder.",
      settingQualityLabel: "MP3 Audio Quality:",
      settingApiLabel: "Spotify API Keys (Optional):",
      settingApiDesc: "API keys are not required for standard downloads.",
      btnCancel: "Cancel",
      btnSave: "Save",
      // Toasts
      toastCopied: "Pasted from clipboard!",
      toastNoClipboard: "Clipboard permission not granted.",
      toastFetched: "{count} tracks fetched successfully!",
      toastBatchQueued: "{count} tracks in batch added to queue.",
      toastAllQueued: "{count} tracks added to download queue.",
      toastSingleQueued: '"{title}" added to queue.',
      toastCancelled: "Downloads stopped.",
      toastFolderSet: "Download folder set to: {path}",
      toastFolderOpened: "Folder opened: {path}",
      toastFolderError: "Could not open folder.",
      toastSettingsSaved: "Settings saved successfully!",
      toastThemeDark: "Dark theme enabled.",
      toastThemeLight: "Light theme enabled.",
      toastLangSwitched: "Language switched to English.",
    },
  };

  function t(key, vars = {}) {
    let str = (i18n[currentLang] && i18n[currentLang][key]) || i18n["en"][key] || key;
    for (const [k, v] of Object.entries(vars)) {
      str = str.replace(new RegExp(`\\{${k}\\}`, "g"), v);
    }
    return str;
  }

  // DOM Elements
  const htmlDoc = document.documentElement;
  const langToggleBtn = document.getElementById("lang-toggle");
  const langLabelText = document.getElementById("lang-label-text");
  const themeToggleBtn = document.getElementById("theme-toggle");
  const themeIcon = document.getElementById("theme-icon");
  const themeLabelText = document.getElementById("theme-label-text");

  const heroTitle = document.getElementById("hero-title");
  const fetchForm = document.getElementById("fetch-form");
  const spotifyUrlInput = document.getElementById("spotify-url-input");
  const btnPaste = document.getElementById("btn-paste");
  const btnPasteText = document.getElementById("btn-paste-text");
  const btnFetch = document.getElementById("btn-fetch");
  const btnFetchText = document.getElementById("btn-fetch-text");
  const btnFetchIcon = document.getElementById("btn-fetch-icon");
  const fetchSpinner = document.getElementById("fetch-spinner");
  const sampleLinksLabel = document.getElementById("sample-links-label");
  const sampleChips = document.querySelectorAll(".sample-chip");

  const emptyState = document.getElementById("empty-state");
  const emptyTitle = document.getElementById("empty-title");
  const emptyDesc = document.getElementById("empty-desc");

  const playlistSection = document.getElementById("playlist-section");
  const plCover = document.getElementById("pl-cover");
  const plBadge = document.getElementById("pl-badge");
  const plTypeLabel = document.getElementById("pl-type-label");
  const plTitle = document.getElementById("pl-title");
  const plDesc = document.getElementById("pl-desc");
  const plOwner = document.getElementById("pl-owner");
  const plTrackCount = document.getElementById("pl-track-count");
  const labelTracksCount = document.getElementById("label-tracks-count");
  const plTotalDuration = document.getElementById("pl-total-duration");
  const plDestFolder = document.getElementById("pl-dest-folder");
  const btnChangeFolderBadge = document.getElementById("btn-change-folder-badge");

  // Folder Selection Elements
  const btnSelectFolder = document.getElementById("btn-select-folder");
  const navFolderLabel = document.getElementById("nav-folder-label");
  const btnHeaderOpenFolder = document.getElementById("btn-open-folder");
  const folderPickerModal = document.getElementById("folder-picker-modal");
  const folderModalTitle = document.getElementById("folder-modal-title");
  const btnCloseFolderModal = document.getElementById("btn-close-folder-modal");
  const btnDoneFolderModal = document.getElementById("btn-done-folder-modal");
  const btnDoneFolderText = document.getElementById("btn-done-folder-text");
  const currentFolderLabel = document.getElementById("current-folder-label");
  const currentFolderDisplay = document.getElementById("current-folder-display");
  const btnOpenCurrentInExplorer = document.getElementById("btn-open-current-in-explorer");
  const btnOpenFolderModalText = document.getElementById("btn-open-folder-modal-text");
  const btnBrowseNativeFolder = document.getElementById("btn-browse-native-folder");
  const btnBrowseNativeText = document.getElementById("btn-browse-native-text");
  const labelQuickLocations = document.getElementById("label-quick-locations");
  const folderPresetsContainer = document.getElementById("folder-presets-container");
  const labelCustomPath = document.getElementById("label-custom-path");
  const customFolderPathInput = document.getElementById("custom-folder-path-input");
  const btnApplyCustomPath = document.getElementById("btn-apply-custom-path");
  const btnApplyPathText = document.getElementById("btn-apply-path-text");

  // Batch Tabs Elements
  const batchTabsContainer = document.getElementById("batch-tabs-container");
  const labelBatches = document.getElementById("label-batches");
  const batchTabsList = document.getElementById("batch-tabs-list");
  const btnDownloadActiveBatch = document.getElementById("btn-download-active-batch");
  const btnBatchDownloadText = document.getElementById("btn-batch-download-text");

  const btnDownloadAll = document.getElementById("btn-download-all");
  const btnDownloadAllText = document.getElementById("btn-download-all-text");
  const btnCancelAll = document.getElementById("btn-cancel-all");
  const btnCancelAllText = document.getElementById("btn-cancel-all-text");
  const selectedCountLabel = document.getElementById("selected-count-label");

  const labelProgress = document.getElementById("label-progress");
  const overallProgressBar = document.getElementById("overall-progress-bar");
  const overallPercentText = document.getElementById("overall-percent-text");
  const overallStatsText = document.getElementById("overall-stats-text");

  const selectAllCheckbox = document.getElementById("select-all-checkbox");
  const labelSelectVisible = document.getElementById("label-select-visible");
  const selectedBadge = document.getElementById("selected-badge");
  const trackFilterInput = document.getElementById("track-filter-input");
  const thTrack = document.getElementById("th-track");
  const thAlbum = document.getElementById("th-album");
  const thStatus = document.getElementById("th-status");
  const thAction = document.getElementById("th-action");
  const tracksTbody = document.getElementById("tracks-tbody");

  // Settings Modal Elements
  const settingsModal = document.getElementById("settings-modal");
  const settingsModalTitle = document.getElementById("settings-modal-title");
  const btnSettingsOpen = document.getElementById("btn-settings-open");
  const btnCloseSettings = document.getElementById("btn-close-settings");
  const btnCancelSettings = document.getElementById("btn-cancel-settings");
  const btnCancelSettingsText = document.getElementById("btn-cancel-settings-text");
  const btnSaveSettings = document.getElementById("btn-save-settings");
  const btnSaveSettingsText = document.getElementById("btn-save-settings-text");
  const labelSettingDir = document.getElementById("label-setting-dir");
  const settingOutputDir = document.getElementById("setting-output-dir");
  const btnOpenDirSettings = document.getElementById("btn-open-dir-settings");
  const btnOpenDirSettingsText = document.getElementById("btn-open-dir-settings-text");
  const labelSettingDirDesc = document.getElementById("label-setting-dir-desc");
  const labelSettingQuality = document.getElementById("label-setting-quality");
  const settingBitrate = document.getElementById("setting-bitrate");
  const labelSettingApi = document.getElementById("label-setting-api");
  const settingClientId = document.getElementById("setting-client-id");
  const settingClientSecret = document.getElementById("setting-client-secret");
  const labelSettingApiDesc = document.getElementById("label-setting-api-desc");

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
     1. INTERNATIONALIZATION (TR / EN)
     ========================================== */
  function applyLanguage(lang) {
    currentLang = lang;
    localStorage.setItem("mp3fy_lang", lang);
    htmlDoc.setAttribute("lang", lang);

    if (langLabelText) langLabelText.textContent = t("langBadge");
    if (langToggleBtn) langToggleBtn.title = t("langTitle");

    // Theme label
    const isDark = htmlDoc.classList.contains("dark");
    if (themeLabelText) themeLabelText.textContent = isDark ? t("themeDark") : t("themeLight");
    if (themeToggleBtn) themeToggleBtn.title = t("themeTitle");

    // Nav and hero
    updateFolderUI(appSettings.output_dir);
    if (btnSelectFolder) btnSelectFolder.title = t("navFolderTitle");
    if (btnHeaderOpenFolder) btnHeaderOpenFolder.title = t("openFolderTitle");
    if (heroTitle) heroTitle.textContent = t("heroTitle");
    if (spotifyUrlInput) spotifyUrlInput.placeholder = t("urlPlaceholder");
    if (btnPasteText) btnPasteText.textContent = t("btnPaste");
    if (btnFetchText && !btnFetch.disabled) btnFetchText.textContent = t("btnFetch");
    if (sampleLinksLabel) {
      sampleLinksLabel.innerHTML = `<span class="material-symbols-outlined text-xs">lightbulb</span> ${t("sampleLinks")}`;
    }

    // Empty state
    if (emptyTitle) emptyTitle.textContent = t("emptyTitle");
    if (emptyDesc) emptyDesc.textContent = t("emptyDesc");

    // Playlist details
    if (labelTracksCount) labelTracksCount.textContent = t("tracksCountLabel");
    if (btnChangeFolderBadge) btnChangeFolderBadge.title = t("changeFolderTooltip");
    if (btnDownloadAllText) btnDownloadAllText.textContent = t("btnDownloadAll");
    if (btnCancelAllText) btnCancelAllText.textContent = t("btnCancelAll");

    // Batch and table headers
    if (labelBatches) {
      labelBatches.innerHTML = `<span class="material-symbols-outlined text-sm text-primary">layers</span> ${t("batchLabel")}`;
    }
    if (trackFilterInput) trackFilterInput.placeholder = t("filterPlaceholder");
    if (labelProgress) {
      labelProgress.innerHTML = `<span class="material-symbols-outlined text-sm text-primary">pending_actions</span> ${t("progressLabel")}`;
    }
    if (labelSelectVisible) labelSelectVisible.textContent = t("selectVisible");
    if (thTrack) thTrack.textContent = t("thTrack");
    if (thAlbum) thAlbum.textContent = t("thAlbum");
    if (thStatus) thStatus.textContent = t("thStatus");
    if (thAction) thAction.textContent = t("thAction");

    // Folder Modal
    if (folderModalTitle) {
      folderModalTitle.innerHTML = `<span class="material-symbols-outlined text-primary">folder_managed</span> ${t("folderModalTitle")}`;
    }
    if (currentFolderLabel) currentFolderLabel.textContent = t("currentFolderLabel");
    if (btnOpenFolderModalText) btnOpenFolderModalText.textContent = t("btnOpenFolderModal");
    if (btnBrowseNativeText) btnBrowseNativeText.textContent = t("btnBrowseNative");
    if (labelQuickLocations) {
      labelQuickLocations.innerHTML = `<span class="material-symbols-outlined text-xs text-primary">near_me</span> ${t("quickLocations")}`;
    }
    if (labelCustomPath) {
      labelCustomPath.innerHTML = `<span class="material-symbols-outlined text-xs">edit_note</span> ${t("customPathLabel")}`;
    }
    if (btnApplyPathText) btnApplyPathText.textContent = t("btnApplyPath");
    if (btnDoneFolderText) btnDoneFolderText.textContent = t("btnDone");

    // Settings Modal
    if (settingsModalTitle) {
      settingsModalTitle.innerHTML = `<span class="material-symbols-outlined text-primary">tune</span> ${t("settingsTitle")}`;
    }
    if (labelSettingDir) {
      labelSettingDir.innerHTML = `<span class="material-symbols-outlined text-xs">folder</span> ${t("settingDirLabel")}`;
    }
    if (btnOpenDirSettingsText) btnOpenDirSettingsText.textContent = t("btnOpenFolderModal");
    if (labelSettingDirDesc) {
      labelSettingDirDesc.innerHTML = `${t("settingDirDesc")}`;
    }
    if (labelSettingQuality) {
      labelSettingQuality.innerHTML = `<span class="material-symbols-outlined text-xs">graphic_eq</span> ${t("settingQualityLabel")}`;
    }
    if (labelSettingApi) {
      labelSettingApi.innerHTML = `<span class="material-symbols-outlined text-xs">key</span> ${t("settingApiLabel")}`;
    }
    if (labelSettingApiDesc) {
      labelSettingApiDesc.innerHTML = `${t("settingApiDesc")}`;
    }
    if (btnCancelSettingsText) btnCancelSettingsText.textContent = t("btnCancel");
    if (btnSaveSettingsText) btnSaveSettingsText.textContent = t("btnSave");

    // Re-render batches & table if playlist loaded
    if (currentPlaylist) {
      renderBatchTabs(currentPlaylist);
      renderTracksTable();
      updateOverallProgress();
    }
  }

  langToggleBtn.addEventListener("click", () => {
    const newLang = currentLang === "tr" ? "en" : "tr";
    applyLanguage(newLang);
    showToast(t("toastLangSwitched"), "info");
  });

  /* ==========================================
     2. THEME TOGGLE (Siyah / Beyaz Tema)
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
      if (themeLabelText) themeLabelText.textContent = t("themeDark");
    } else {
      htmlDoc.classList.remove("dark");
      htmlDoc.setAttribute("data-theme", "light");
      if (themeIcon) themeIcon.textContent = "light_mode";
      if (themeLabelText) themeLabelText.textContent = t("themeLight");
    }
    localStorage.setItem("mp3fy_theme", theme);
  }

  themeToggleBtn.addEventListener("click", () => {
    const isDark = htmlDoc.classList.contains("dark");
    const newTheme = isDark ? "light" : "dark";
    setTheme(newTheme);
    showToast(newTheme === "dark" ? t("toastThemeDark") : t("toastThemeLight"), "info");
  });

  /* ==========================================
     3. WEBSOCKET CONNECTION
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
     4. SETTINGS & FOLDER SELECTION
     ========================================== */
  function updateFolderUI(folderPath) {
    if (!folderPath) return;
    appSettings.output_dir = folderPath;

    let shortName = folderPath;
    const parts = folderPath.replace(/\\/g, "/").split("/").filter(Boolean);
    if (parts.length > 0) {
      shortName = parts[parts.length - 1];
    }

    if (navFolderLabel) navFolderLabel.textContent = `${t("folderPrefix")}: ${shortName}`;
    if (currentFolderDisplay) currentFolderDisplay.textContent = folderPath;
    if (plDestFolder) plDestFolder.textContent = folderPath;
    if (settingOutputDir) settingOutputDir.value = folderPath;
    if (customFolderPathInput) customFolderPathInput.value = folderPath;
  }

  async function loadSettings() {
    try {
      const res = await fetch("/api/settings");
      const data = await res.json();
      appSettings = data;
      updateFolderUI(data.output_dir);
      settingBitrate.value = data.bitrate;
      if (data.spotify_client_id) settingClientId.value = data.spotify_client_id;
    } catch (e) {
      console.error("Error loading settings:", e);
    }
  }

  async function loadFolderPresets() {
    try {
      const res = await fetch("/api/folder-presets");
      const data = await res.json();
      const presets = data.presets || [];
      folderPresetsContainer.innerHTML = "";

      presets.forEach((preset) => {
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className =
          "bg-surface-container hover:bg-surface-container-high text-on-surface p-2.5 rounded-xl border border-white/5 flex items-center gap-2 text-xs font-label-md transition-all text-left truncate";
        
        let displayName = preset.name;
        if (currentLang === "en") {
          if (preset.name === "Müzik") displayName = "Music";
          else if (preset.name === "İndirilenler") displayName = "Downloads";
          else if (preset.name === "Masaüstü") displayName = "Desktop";
          else if (preset.name === "Belgeler") displayName = "Documents";
        }

        btn.innerHTML = `
          <span class="material-symbols-outlined text-primary text-sm">${preset.icon || "folder"}</span>
          <span class="truncate font-semibold">${displayName}</span>
        `;
        btn.addEventListener("click", async () => {
          await changeDownloadFolder(preset.path);
          showToast(t("toastFolderSet", { path: displayName }), "success");
        });
        folderPresetsContainer.appendChild(btn);
      });
    } catch (e) {
      console.error("Error loading folder presets:", e);
    }
  }

  async function changeDownloadFolder(newPath) {
    if (!newPath) return false;
    try {
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ output_dir: newPath.trim() }),
      });
      const data = await res.json();
      if (res.ok) {
        updateFolderUI(data.settings.output_dir);
        return true;
      }
    } catch (e) {
      console.error("Error setting download folder:", e);
    }
    return false;
  }

  function openFolderPickerModal() {
    loadFolderPresets();
    folderPickerModal.classList.remove("hidden");
  }

  function closeFolderPickerModal() {
    folderPickerModal.classList.add("hidden");
  }

  btnSelectFolder.addEventListener("click", openFolderPickerModal);
  if (btnChangeFolderBadge) btnChangeFolderBadge.addEventListener("click", openFolderPickerModal);
  btnCloseFolderModal.addEventListener("click", closeFolderPickerModal);
  btnDoneFolderModal.addEventListener("click", closeFolderPickerModal);

  // Native OS Browse Button
  btnBrowseNativeFolder.addEventListener("click", async () => {
    btnBrowseNativeFolder.disabled = true;
    btnBrowseNativeFolder.innerHTML = `<span class="spinner inline-block"></span> ${t("btnBrowsingNative")}`;

    try {
      const res = await fetch("/api/browse-folder", { method: "POST" });
      const data = await res.json();
      if (data.status === "success" && data.path) {
        updateFolderUI(data.path);
        showToast(t("toastFolderSet", { path: data.path }), "success");
        closeFolderPickerModal();
      }
    } catch (e) {
      showToast(t("toastFolderError"), "error");
    } finally {
      btnBrowseNativeFolder.disabled = false;
      btnBrowseNativeFolder.innerHTML = `<span class="material-symbols-outlined">drive_folder_upload</span> <span id="btn-browse-native-text">${t("btnBrowseNative")}</span>`;
    }
  });

  // Apply Custom Path
  btnApplyCustomPath.addEventListener("click", async () => {
    const val = customFolderPathInput.value.trim();
    if (!val) {
      showToast("Lütfen geçerli bir klasör yolu girin.", "error");
      return;
    }
    const success = await changeDownloadFolder(val);
    if (success) {
      showToast(t("toastFolderSet", { path: val }), "success");
    } else {
      showToast(t("toastFolderError"), "error");
    }
  });

  // Open Current in Explorer
  btnOpenCurrentInExplorer.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/open-folder", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: appSettings.output_dir }),
      });
      const data = await res.json();
      if (data.status === "success") {
        showToast(t("toastFolderOpened", { path: data.path }), "success");
      }
    } catch (e) {
      showToast(t("toastFolderError"), "error");
    }
  });

  btnHeaderOpenFolder.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/open-folder", { method: "POST" });
      const data = await res.json();
      if (data.status === "success") {
        showToast(t("toastFolderOpened", { path: data.path }), "success");
      }
    } catch (e) {
      showToast(t("toastFolderError"), "error");
    }
  });

  // Settings Modal Handlers
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
        showToast(t("toastSettingsSaved"), "success");
        closeSettingsModal();
        loadSettings();
      } else {
        showToast(data.detail || "Error saving settings.", "error");
      }
    } catch (e) {
      showToast("Error saving settings.", "error");
    }
  });

  btnOpenDirSettings.addEventListener("click", async () => {
    try {
      const res = await fetch("/api/open-folder", { method: "POST" });
      const data = await res.json();
      if (data.status === "success") {
        showToast(t("toastFolderOpened", { path: data.path }), "success");
      }
    } catch (e) {
      showToast(t("toastFolderError"), "error");
    }
  });

  /* ==========================================
     5. URL INPUT & FETCHING
     ========================================== */
  btnPaste.addEventListener("click", async () => {
    try {
      const text = await navigator.clipboard.readText();
      if (text) {
        spotifyUrlInput.value = text.trim();
        showToast(t("toastCopied"), "info");
      }
    } catch (err) {
      showToast(t("toastNoClipboard"), "error");
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
        throw new Error(resData.detail || "Error fetching Spotify metadata.");
      }

      currentPlaylist = resData.data;
      activeBatchIndex = 0;
      renderPlaylist(currentPlaylist);
      showToast(t("toastFetched", { count: currentPlaylist.tracks.length }), "success");
    } catch (err) {
      showToast(err.message, "error");
    } finally {
      setLoadingState(false);
    }
  }

  function setLoadingState(isLoading) {
    if (isLoading) {
      btnFetch.disabled = true;
      btnFetchText.textContent = t("btnFetching");
      if (btnFetchIcon) btnFetchIcon.classList.add("hidden");
      fetchSpinner.classList.remove("hidden");
    } else {
      btnFetch.disabled = false;
      btnFetchText.textContent = t("btnFetch");
      if (btnFetchIcon) btnFetchIcon.classList.remove("hidden");
      fetchSpinner.classList.add("hidden");
    }
  }

  /* ==========================================
     6. RENDER PLAYLIST & 100-TRACK BATCHES
     ========================================== */
  function renderPlaylist(playlist) {
    emptyState.classList.add("hidden");
    playlistSection.classList.remove("hidden");

    // Header info
    plCover.src = playlist.cover_url || "/static/img/placeholder.svg";
    plBadge.textContent = (playlist.type || "playlist").toUpperCase();
    plTypeLabel.textContent = playlist.type === "album" ? t("typeAlbum") : playlist.type === "track" ? t("typeTrack") : t("typePlaylist");
    plTitle.textContent = playlist.title;
    plDesc.textContent = playlist.description || "";
    plOwner.textContent = playlist.owner;
    plTrackCount.textContent = playlist.total_tracks;
    plDestFolder.textContent = appSettings.output_dir;

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
      btnAll.textContent = `${t("batchAll")} (${playlist.tracks.length})`;
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
    btnAll.textContent = `✨ ${t("batchAll")} (${playlist.tracks.length})`;
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
      
      const batchName = `${t("batchPrefix")} ${b.batch_index} (${b.start_index} - ${b.end_index})`;
      btnBatch.textContent = `📦 ${batchName}`;
      btnBatch.addEventListener("click", () => {
        activeBatchIndex = b.batch_index;
        setActiveBatchTab(btnBatch);
        btnDownloadActiveBatch.classList.remove("hidden");
        btnBatchDownloadText.textContent = `${t("btnDownloadBatch")} (${b.count})`;
        renderTracksTable();
      });
      batchTabsList.appendChild(btnBatch);
    });

    if (activeBatchIndex > 0) {
      const currentB = batches.find((b) => b.batch_index === activeBatchIndex);
      if (currentB) {
        btnBatchDownloadText.textContent = `${t("btnDownloadBatch")} (${currentB.count})`;
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
                ? `<button class="p-1.5 hover:bg-surface-container rounded-lg text-primary transition-colors btn-play" data-id="${track.id}" title="${t("btnPreview")}">
                     <span class="material-symbols-outlined text-sm">play_arrow</span>
                   </button>`
                : ""
            }
            <button class="bg-surface-container hover:bg-surface-container-high text-on-surface px-2.5 py-1 rounded-lg text-xs font-label-sm font-semibold transition-colors flex items-center gap-1 btn-download-single border border-white/5" data-id="${track.id}" title="${t("btnDownloadSingle")}">
              <span class="material-symbols-outlined text-xs">download</span>
              <span>${t("btnDownloadSingle")}</span>
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

    document.querySelectorAll(".btn-download-single").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = btn.getAttribute("data-id");
        const song = currentPlaylist.tracks.find((t) => t.id === id);
        if (song) {
          downloadSingleSong(song);
        }
      });
    });

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
      return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-label-sm font-medium bg-surface-container-highest/60 text-on-surface-variant"><span class="w-1.5 h-1.5 rounded-full bg-on-surface-variant/40"></span> ${t("statusReady")}</span>`;
    }

    const s = task.status;
    if (s === "queued") {
      return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-label-sm font-medium bg-surface-container text-on-surface-variant"><span class="material-symbols-outlined text-[12px] animate-pulse">schedule</span> ${t("statusQueued")}</span>`;
    } else if (s === "searching") {
      return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-label-sm font-medium bg-info/20 text-info"><span class="material-symbols-outlined text-[12px] animate-spin">sync</span> ${t("statusSearching")}</span>`;
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
      return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-label-sm font-medium bg-primary/20 text-primary"><span class="material-symbols-outlined text-[12px] animate-spin">settings</span> ${t("statusConverting")}</span>`;
    } else if (s === "tagging") {
      return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-label-sm font-medium bg-cyan-500/20 text-cyan-400"><span class="material-symbols-outlined text-[12px]">label</span> ${t("statusTagging")}</span>`;
    } else if (s === "completed") {
      return `
        <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-label-sm font-bold bg-green-500/20 text-green-400">
          <span class="material-symbols-outlined text-[12px]">check_circle</span> ${t("statusCompleted")} ${task.file_size_mb ? `(${task.file_size_mb} MB)` : ""}
        </span>
      `;
    } else if (s === "error") {
      return `
        <span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-label-sm font-bold bg-error/20 text-error" title="${escapeHtml(task.error_message || t("statusError"))}">
          <span class="material-symbols-outlined text-[12px]">error</span> ${t("statusError")}
        </span>
      `;
    } else if (s === "cancelled") {
      return `<span class="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-label-sm bg-surface-container text-on-surface-variant"><span class="material-symbols-outlined text-[12px]">block</span> ${t("statusCancelled")}</span>`;
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
     7. SELECTION & FILTERING
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
    selectedBadge.textContent = t("selectedBadge", { count });
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
     8. DOWNLOAD DISPATCH
     ========================================== */
  async function downloadSingleSong(song) {
    try {
      showToast(t("toastSingleQueued", { title: song.title }), "info");
      const res = await fetch("/api/download/single", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ song, output_dir: appSettings.output_dir }),
      });
      const data = await res.json();
      if (res.ok) {
        currentTasks[song.id] = data.task;
        updateTrackRow(data.task);
      }
    } catch (e) {
      showToast("Download could not be started.", "error");
    }
  }

  btnDownloadActiveBatch.addEventListener("click", async () => {
    if (!currentPlaylist) return;
    const batchTracks = currentPlaylist.tracks.filter(
      (t) => activeBatchIndex === 0 || t.batch_index === activeBatchIndex
    );
    const toDownload = batchTracks.filter((t) => selectedSongIds.has(t.id));

    if (toDownload.length === 0) {
      showToast(t("selectedBadge", { count: 0 }), "error");
      return;
    }

    showToast(t("toastBatchQueued", { count: toDownload.length }), "success");
    btnCancelAll.classList.remove("hidden");

    try {
      const res = await fetch("/api/download/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ songs: toDownload, output_dir: appSettings.output_dir }),
      });
      const data = await res.json();
      if (res.ok && data.tasks) {
        data.tasks.forEach((t) => {
          currentTasks[t.id] = t;
          updateTrackRow(t);
        });
      }
    } catch (e) {
      showToast("Batch download error.", "error");
    }
  });

  btnDownloadAll.addEventListener("click", async () => {
    if (!currentPlaylist || selectedSongIds.size === 0) return;

    const songsToDownload = currentPlaylist.tracks.filter((t) => selectedSongIds.has(t.id));
    showToast(t("toastAllQueued", { count: songsToDownload.length }), "success");

    btnCancelAll.classList.remove("hidden");

    try {
      const res = await fetch("/api/download/batch", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ songs: songsToDownload, output_dir: appSettings.output_dir }),
      });
      const data = await res.json();
      if (res.ok && data.tasks) {
        data.tasks.forEach((t) => {
          currentTasks[t.id] = t;
          updateTrackRow(t);
        });
      }
    } catch (e) {
      showToast("Download error.", "error");
    }
  });

  btnCancelAll.addEventListener("click", async () => {
    try {
      await fetch("/api/cancel-all", { method: "POST" });
      showToast(t("toastCancelled"), "info");
      btnCancelAll.classList.add("hidden");
    } catch (e) {
      showToast("Cancel failed.", "error");
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
    
    let stats = t("completedStats", { completed, total });
    if (inProgress > 0) {
      stats += " " + t("downloadingStats", { count: inProgress });
    }
    overallStatsText.textContent = stats;

    if (inProgress === 0 && completed > 0) {
      btnCancelAll.classList.add("hidden");
    }
  }

  /* ==========================================
     9. FLOATING AUDIO PLAYER
     ========================================== */
  function playAudioPreview(song, task) {
    let audioSrc = "";
    if (task && task.status === "completed" && task.file_path) {
      audioSrc = `/api/music/file?path=${encodeURIComponent(task.file_path)}`;
    } else if (song.preview_url) {
      audioSrc = song.preview_url;
    }

    if (!audioSrc) {
      showToast("No audio preview available for this track.", "error");
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
     10. TOAST NOTIFICATIONS
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
     11. HELPERS
     ========================================== */
  function formatDuration(ms) {
    if (!ms || ms <= 0) return "0:00";
    const totalSec = Math.floor(ms / 1000);
    const hrs = Math.floor(totalSec / 3600);
    const mins = Math.floor((totalSec % 3600) / 60);
    const secs = totalSec % 60;
    if (hrs > 0) {
      return currentLang === "en" ? `${hrs} hr ${mins} min` : `${hrs} sa ${mins} dk`;
    }
    return currentLang === "en" ? `${mins} min ${secs} sec` : `${mins} dk ${secs} sn`;
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
  applyLanguage(currentLang);
  initWebSocket();
  loadSettings();
});
