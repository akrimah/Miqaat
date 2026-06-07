/** Prayer Times web UI */

const form = document.getElementById("form");
const errorEl = document.getElementById("error");
const resultsEl = document.getElementById("results");
const todayCard = document.getElementById("today-card");
const daysList = document.getElementById("days-list");
const resultsTitle = document.getElementById("results-title");
const resultsMeta = document.getElementById("results-meta");
const submitBtn = document.getElementById("submit");
const submitText = document.getElementById("submit-text");
const submitSpinner = document.getElementById("submit-spinner");
const downloadBtn = document.getElementById("download-ics");
const methodSelect = document.getElementById("method");
const detectBtn = document.getElementById("detect-location");
const coordsLabel = document.getElementById("coords-label");
const cityFields = document.getElementById("city-fields");
const locationFields = document.getElementById("location-fields");
const segments = document.querySelectorAll(".segment");

let mode = "city";
let coords = null;
let lastRequest = null;
let lastResult = null;

function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

function addDaysISO(iso, days) {
  const d = new Date(iso + "T12:00:00");
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}

function initDates() {
  const start = document.getElementById("start");
  const end = document.getElementById("end");
  start.value = todayISO();
  end.value = addDaysISO(todayISO(), 30);
  start.min = "2020-01-01";
  end.min = start.value;
  start.addEventListener("change", () => {
    end.min = start.value;
    if (end.value < start.value) end.value = start.value;
  });
}

function showError(message) {
  errorEl.textContent = message;
  errorEl.classList.remove("hidden");
}

function hideError() {
  errorEl.classList.add("hidden");
  errorEl.textContent = "";
}

function setLoading(loading) {
  submitBtn.disabled = loading;
  submitText.classList.toggle("hidden", loading);
  submitSpinner.classList.toggle("hidden", !loading);
}

function setMode(newMode) {
  mode = newMode;
  segments.forEach((btn) => {
    const active = btn.dataset.mode === newMode;
    btn.classList.toggle("active", active);
    btn.setAttribute("aria-selected", active);
  });
  cityFields.classList.toggle("hidden", newMode !== "city");
  locationFields.classList.toggle("hidden", newMode !== "location");
}

segments.forEach((btn) => {
  btn.addEventListener("click", () => setMode(btn.dataset.mode));
});

async function loadMethods() {
  try {
    const res = await fetch("/api/methods");
    if (!res.ok) throw new Error("Could not load calculation methods");
    const methods = await res.json();
    methodSelect.innerHTML = methods
      .map((m) => `<option value="${m.id}">${m.name}</option>`)
      .join("");
    methodSelect.value = "2";
  } catch {
    methodSelect.innerHTML = '<option value="2">ISNA (default)</option>';
  }
}

function buildRequest() {
  const start = document.getElementById("start").value;
  const end = document.getElementById("end").value;
  const method = parseInt(methodSelect.value, 10);
  const school = parseInt(document.querySelector('input[name="school"]:checked').value, 10);

  let location;
  if (mode === "city") {
    const city = document.getElementById("city").value.trim();
    const country = document.getElementById("country").value.trim();
    if (!city || !country) {
      throw new Error("Please enter both city and country");
    }
    location = { city, country };
  } else {
    if (!coords) {
      throw new Error("Please detect your location first");
    }
    location = { latitude: coords.lat, longitude: coords.lon };
  }

  return { location, start, end, method, school };
}

function locationLabel(data) {
  const loc = data.location;
  if (loc.city) return `${loc.city}, ${loc.country}`;
  return `${loc.latitude.toFixed(4)}, ${loc.longitude.toFixed(4)}`;
}

function formatDate(iso) {
  const d = new Date(iso + "T12:00:00");
  return d.toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

async function parseError(res) {
  const body = await res.json();
  const detail = body.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join("; ");
  }
  return "Request failed";
}

function prayerGridHTML(prayers) {
  return `<div class="prayer-grid">${prayers
    .map(
      (p) =>
        `<div class="prayer-item"><span class="prayer-name">${p.name}</span><span class="prayer-time">${p.time}</span></div>`
    )
    .join("")}</div>`;
}

function renderResults(data) {
  lastResult = data;
  const label = locationLabel(data);
  const tz = data.days[0]?.timezone ?? "";
  resultsTitle.textContent = label;
  resultsMeta.textContent = `${data.days.length} day${data.days.length === 1 ? "" : "s"} · ${tz}`;

  const today = todayISO();
  const todayDay = data.days.find((d) => d.date === today);
  const otherDays = data.days.filter((d) => d.date !== today);

  if (todayDay) {
    todayCard.innerHTML = `<h3>Today</h3>${prayerGridHTML(todayDay.prayers)}`;
    todayCard.classList.remove("hidden");
  } else {
    todayCard.classList.add("hidden");
  }

  daysList.innerHTML = otherDays
    .map(
      (day) =>
        `<article class="day-card"><div class="day-date">${formatDate(day.date)}</div>${prayerGridHTML(day.prayers)}</article>`
    )
    .join("");

  resultsEl.classList.remove("hidden");
}

function isSecureContext() {
  return window.isSecureContext || location.hostname === "localhost" || location.hostname === "127.0.0.1";
}

function getPosition(options) {
  return new Promise((resolve, reject) => {
    navigator.geolocation.getCurrentPosition(resolve, reject, options);
  });
}

/** Try cached/low-accuracy first, then a fresh fix with a longer timeout. */
async function detectCurrentPosition() {
  // Cached position (up to 10 min) — often instant on repeat visits
  try {
    return await getPosition({
      enableHighAccuracy: false,
      maximumAge: 600_000,
      timeout: 20_000,
    });
  } catch (err) {
    if (err.code !== 3) throw err; // not a timeout — pass through
  }

  // Fresh network/Wi‑Fi fix — longer wait for desktop and indoor use
  try {
    return await getPosition({
      enableHighAccuracy: false,
      maximumAge: 0,
      timeout: 45_000,
    });
  } catch (err) {
    if (err.code !== 3) throw err;
  }

  // Last resort: GPS (slower indoors but can succeed when network location fails)
  return getPosition({
    enableHighAccuracy: true,
    maximumAge: 0,
    timeout: 45_000,
  });
}

function geolocationErrorMessage(err) {
  const messages = {
    1: "Location permission denied. Allow location access in your browser settings, or enter a city instead.",
    2: "Location unavailable. Try again or enter a city and country.",
    3: "Location took too long. Move near a window, check Wi‑Fi is on, or enter a city instead.",
  };
  return messages[err.code] || "Could not get your location. Try entering a city instead.";
}

detectBtn.addEventListener("click", async () => {
  hideError();
  if (!navigator.geolocation) {
    showError("Geolocation is not supported by your browser");
    return;
  }
  if (!isSecureContext()) {
    showError("Location requires HTTPS. Use city search, or open this site over a secure connection.");
    return;
  }

  detectBtn.disabled = true;
  detectBtn.textContent = "Detecting…";
  coordsLabel.textContent = "Finding your location — can take up to a minute indoors";
  coordsLabel.classList.remove("hidden");

  try {
    const pos = await detectCurrentPosition();
    coords = { lat: pos.coords.latitude, lon: pos.coords.longitude };
    coordsLabel.textContent = `Using ${coords.lat.toFixed(4)}, ${coords.lon.toFixed(4)}`;
    detectBtn.textContent = "Update location";
    setMode("location");
  } catch (err) {
    coordsLabel.classList.add("hidden");
    detectBtn.textContent = "Use my current location";
    showError(geolocationErrorMessage(err));
  } finally {
    detectBtn.disabled = false;
  }
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  hideError();
  setLoading(true);

  try {
    lastRequest = buildRequest();
    const res = await fetch("/api/prayer-times", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(lastRequest),
    });
    if (!res.ok) throw new Error(await parseError(res));
    const body = await res.json();
    renderResults(body);
  } catch (err) {
    showError(err.message || "Something went wrong");
  } finally {
    setLoading(false);
  }
});

downloadBtn.addEventListener("click", async () => {
  if (!lastRequest) return;
  hideError();
  downloadBtn.disabled = true;

  try {
    const res = await fetch("/api/export/ics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(lastRequest),
    });
    if (!res.ok) throw new Error(await parseError(res));
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "prayer-times.ics";
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    showError(err.message || "Could not download calendar");
  } finally {
    downloadBtn.disabled = false;
  }
});

initDates();
loadMethods();
