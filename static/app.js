document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) lucide.createIcons();

  const textarea = document.getElementById("question");
  const runBtn = document.getElementById("runBtn");
  const sectionsDiv = document.getElementById("sections");
  const sectionInput = document.getElementById("sectionInput");
  const addSectionBtn = document.getElementById("addSection");
  const results = document.getElementById("results");
  const historySelect = document.getElementById("historySelect");
  const refreshHistory = document.getElementById("refreshHistory");
  const micBtn = document.getElementById("micbtn");

  let sections = ["Answer", "Explanation", "Why this"];

  // --- Auto Expand Textarea ---
  textarea.addEventListener("input", () => {
    textarea.style.height = "auto";
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + "px";
  });

  // --- Section Chips ---
  function renderChips() {
    sectionsDiv.innerHTML = "";
    sections.forEach((s, i) => {
      const div = document.createElement("div");
      div.className = "chip";
      div.innerHTML = `${s} <span onclick="removeSection(${i})">x</span>`;
      sectionsDiv.appendChild(div);
    });
  }

  window.removeSection = (i) => {
    sections.splice(i, 1);
    renderChips();
  };

  addSectionBtn.addEventListener("click", () => {
    const val = sectionInput.value.trim();
    if (val && !sections.includes(val)) sections.push(val);
    sectionInput.value = "";
    renderChips();
  });

  // --- History Loading ---
  async function loadHistoryList() {
    try {
      const r = await fetch("/api/history");
      const j = await r.json();
      historySelect.innerHTML = `<option value="">Select a session...</option>`;
      (j.sessions || []).forEach((s) => {
        const opt = document.createElement("option");
        const when = new Date(s.ts || 0).toLocaleString();
        opt.value = s.id;
        opt.textContent = `${when} — ${s.title}`;
        historySelect.appendChild(opt);
      });
    } catch (_) {}
  }

  refreshHistory.addEventListener("click", loadHistoryList);

  historySelect.addEventListener("change", async () => {
    const id = historySelect.value;
    if (!id) return;
    const r = await fetch(`/api/history/${id}`);
    const j = await r.json();
    if (j.error) return;

    results.innerHTML = "";
    appendMessage("user", j.question || "(no question)");
    const loadedSections = j.sections || [];
    const loadedAnswers = j.answers || {};
    sections = loadedSections.length ? loadedSections : sections;
    renderChips();
    Object.entries(loadedAnswers).forEach(([k, v]) => {
      appendMessage("ai", `**${k}**: ${v}`);
    });
  });

  // --- Run Query ---
  runBtn.addEventListener("click", async () => {
    const question = textarea.value.trim();
    if (!question) return alert("Please type your question.");
    appendMessage("user", question);
    textarea.value = "";
    textarea.style.height = "auto";

    const res = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, sections }),
    });

    const data = await res.json();
    Object.entries(data.sections || {}).forEach(([k, v]) => {
      appendMessage("ai", `**${k}**: ${v}`);
      speakText(v); // Speak response
    });
    loadHistoryList();
  });

  // --- Append Message ---
  function appendMessage(type, text) {
    const div = document.createElement("div");
    div.className = `message ${type}`;
    div.innerHTML = text.replace(/\n/g, "<br>");
    results.appendChild(div);
    results.scrollTop = results.scrollHeight;
  }

  // --- TEXT TO SPEECH (AI Voice) ---
  async function speakText(text) {
    try {
      const res = await fetch("/api/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const data = await res.json();
      if (data.audio_b64) {
        const audio = new Audio(`data:audio/mp3;base64,${data.audio_b64}`);
        audio.play();
      }
    } catch (err) {
      console.error("TTS failed:", err);
    }
  }

  // --- SPEECH TO TEXT (MIC) ---
  let mediaRecorder;
  let audioChunks = [];

  if (micBtn) {
    micBtn.addEventListener("click", async () => {
      if (mediaRecorder && mediaRecorder.state === "recording") {
        mediaRecorder.stop();
        micBtn.innerText = "🎙️";
        return;
      }

      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];

        mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);

        mediaRecorder.onstop = async () => {
          const blob = new Blob(audioChunks, { type: "audio/wav" });
          const formData = new FormData();
          formData.append("audio", blob, "input.wav");

          const res = await fetch("/api/stt", { method: "POST", body: formData });
          const data = await res.json();

          if (data && data.text) {
            textarea.value = data.text;
          } else {
            alert("Speech recognition failed.");
          }
        };

        mediaRecorder.start();
        micBtn.innerText = "⏹️"; // stop icon
      } catch (err) {
        alert("Microphone access denied or unavailable.");
        console.error(err);
      }
    });
  }

  renderChips();
  loadHistoryList();
});
