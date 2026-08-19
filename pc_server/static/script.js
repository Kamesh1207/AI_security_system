// ============================================
// AI Smart Security Dashboard — Vanilla JS
// No CDN dependencies required
// ============================================

(function () {
  'use strict';

  // DOM element cache
  const $ = (id) => document.getElementById(id);

  const els = {
    hwDot: $('hw-dot'), hwLabel: $('hw-label'),
    statusDot: $('status-dot'), statusLabel: $('status-label'),
    threatBanner: $('threat-banner'), threatMessage: $('threat-message'),
    motionOverlay: $('motion-overlay'), cameraTs: $('camera-ts'),
    snapshotImg: $('snapshot-img'), snapshotTs: $('snapshot-ts'),
    lockCircle: $('lock-circle'), lockIcon: $('lock-icon'),
    lockTitle: $('lock-title'), lockDetail: $('lock-detail'), lockCard: $('lock-card'),
    keypadDisplay: $('keypad-display'), keypadDot: $('keypad-dot'),
    keypadStatusText: $('keypad-status-text'),
    soundValue: $('sound-value'), rfidValue: $('rfid-value'), motionValue: $('motion-value'),
    logsContainer: $('logs-container'), logCountBadge: $('log-count-badge'),
  };

  // ============================================
  // SSE Connection with auto-reconnect
  // ============================================
  let eventSource = null;
  let reconnectTimer = null;

  function connectSSE() {
    if (eventSource) { try { eventSource.close(); } catch (_) {} }

    eventSource = new EventSource('/stream-events');

    eventSource.onmessage = function (e) {
      try {
        const state = JSON.parse(e.data);
        updateDashboard(state);
      } catch (err) {
        console.error('[SSE] Parse error:', err);
      }
    };

    eventSource.onerror = function () {
      console.warn('[SSE] Connection lost. Reconnecting in 3s...');
      els.statusLabel.textContent = 'CONNECTION ERROR';
      els.statusLabel.className = 'status-label text-glow-red';
      setDotClass(els.statusDot, 'red');
      if (eventSource) { try { eventSource.close(); } catch (_) {} }
      clearTimeout(reconnectTimer);
      reconnectTimer = setTimeout(connectSSE, 3000);
    };
  }

  // ============================================
  // Dashboard state renderer
  // ============================================
  function updateDashboard(s) {
    // Hardware badge
    if (s.hardware_online) {
      setDotClass(els.hwDot, 'green');
      els.hwLabel.textContent = 'ESP32 ONLINE';
      els.hwLabel.className = 'hw-label text-glow-green';
    } else {
      setDotClass(els.hwDot, 'red');
      els.hwLabel.textContent = 'ESP32 OFFLINE';
      els.hwLabel.className = 'hw-label text-glow-red';
    }

    // System status badge
    const alarmActive = s.alarm_active;
    const statusColor = alarmActive ? 'red' : s.system_status === 'MONITORING' ? 'green' : 'cyan';
    setDotClass(els.statusDot, statusColor);
    els.statusLabel.textContent = s.system_status || 'MONITORING';
    els.statusLabel.className = 'status-label text-glow-' + statusColor;

    // Threat banner
    if (alarmActive) {
      els.threatBanner.classList.remove('hidden');
      els.threatMessage.textContent = s.latest_incident || 'Suspicious activity detected in secure zone.';
    } else {
      els.threatBanner.classList.add('hidden');
    }

    // Motion overlay on camera
    if (s.motion_detected) {
      els.motionOverlay.classList.remove('hidden');
    } else {
      els.motionOverlay.classList.add('hidden');
    }

    // Camera timestamp
    els.cameraTs.textContent = 'CAM_01 // ' + new Date().toLocaleTimeString();

    // Snapshot
    if (s.latest_image) {
      els.snapshotImg.src = '/captured_images/' + s.latest_image;
      els.snapshotImg.alt = 'Incident Snapshot';
      // Parse timestamp from filename
      const parts = s.latest_image.split('_');
      if (parts.length >= 3) {
        const d = parts[1], t = parts[2];
        els.snapshotTs.textContent = d.substring(0,4)+'-'+d.substring(4,6)+'-'+d.substring(6,8)+' '+t.substring(0,2)+':'+t.substring(2,4)+':'+t.substring(4,6);
      }
    } else {
      els.snapshotImg.src = '';
      els.snapshotImg.alt = 'No Incidents';
      els.snapshotTs.textContent = 'N/A';
    }

    // Lock widget
    if (s.door_locked) {
      els.lockCircle.className = 'lock-circle lock-circle-locked';
      els.lockIcon.innerHTML = '&#128274;';
      els.lockTitle.textContent = 'SECURE ZONE LOCKED';
      els.lockTitle.className = 'lock-title text-glow-red';
      els.lockDetail.textContent = 'Relay GPIO 21 — LOW (Secured)';
      els.lockCard.style.borderColor = '';
    } else {
      els.lockCircle.className = 'lock-circle lock-circle-unlocked';
      els.lockIcon.innerHTML = '&#128275;';
      els.lockTitle.textContent = 'ZONE UNLOCKED';
      els.lockTitle.className = 'lock-title text-glow-green';
      els.lockDetail.textContent = 'Relay GPIO 21 — HIGH (5s Timer Active)';
      els.lockCard.style.borderColor = 'rgba(57,255,20,0.3)';
    }

    // Keypad terminal
    updateKeypad(s.system_status, s.password_status);

    // Sensor telemetry
    els.soundValue.textContent = s.sound_value || 0;
    els.soundValue.className = 'metric-value' + (s.sound_value > 1500 ? ' text-glow-orange' : '');

    const rfid = s.rfid_status || 'IDLE';
    els.rfidValue.textContent = rfid;
    els.rfidValue.className = 'metric-value' + (rfid.includes('AUTHORIZED') ? ' text-glow-green' : rfid.includes('REJECTED') ? ' text-glow-red' : '');

    els.motionValue.textContent = s.motion_detected ? 'PRESENCE DETECTED' : 'NO PRESENCE';
    els.motionValue.className = 'metric-value' + (s.motion_detected ? ' text-glow-green' : '');

    // Logs
    updateLogs(s.recent_logs || []);
  }

  function updateKeypad(systemStatus, passwordStatus) {
    let display = '—— LOCKED ——';
    let statusText = 'Awaiting RFID Authentication';
    let colorClass = '';
    let dotColor = 'gray';

    if (systemStatus === 'ENTER PASSWORD' || passwordStatus) {
      display = passwordStatus || '****';
      statusText = 'Enter PIN and press [#]';
      colorClass = 'active-cyan';
      dotColor = 'cyan';
    } else if (systemStatus === 'ACCESS GRANTED') {
      display = '✓ GRANTED';
      statusText = 'Credentials Approved';
      colorClass = 'active-green';
      dotColor = 'green';
    } else if (systemStatus === 'ACCESS DENIED') {
      display = '✗ DENIED';
      statusText = 'Invalid Credentials';
      colorClass = 'active-red';
      dotColor = 'red';
    }

    els.keypadDisplay.textContent = display;
    els.keypadDisplay.className = 'keypad-display ' + colorClass;
    els.keypadStatusText.textContent = statusText;
    setDotClass(els.keypadDot, dotColor);
  }

  function updateLogs(logs) {
    els.logCountBadge.textContent = logs.length + ' EVENTS';

    if (logs.length === 0) {
      els.logsContainer.innerHTML = '<div class="logs-empty">&#128752; Awaiting events...</div>';
      return;
    }

    let html = '';
    for (let i = 0; i < logs.length; i++) {
      const log = logs[i];
      const cat = log.category || 'ACCESS';
      html += '<div class="log-entry cat-' + cat + '">'
        + '<span class="log-ts">' + escapeHtml(log.timestamp) + '</span>'
        + '<span class="log-badge log-badge-' + cat + '">' + cat + '</span>'
        + '<span class="log-msg' + (cat === 'INTRUSION' ? ' log-msg-INTRUSION' : '') + '">' + escapeHtml(log.message) + '</span>'
        + '</div>';
    }
    els.logsContainer.innerHTML = html;
  }

  // ============================================
  // Utilities
  // ============================================
  function setDotClass(el, color) {
    if (!el) return;
    el.className = 'status-dot status-dot-' + color + ' pulse-ring';
  }

  function escapeHtml(str) {
    if (!str) return '';
    const map = { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#039;' };
    return String(str).replace(/[&<>"']/g, function (c) { return map[c]; });
  }

  // ============================================
  // Global: Reset Alarm
  // ============================================
  window.resetAlarm = function () {
    fetch('/api/reset-alarm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    }).catch(function (err) { console.error('[ALARM] Reset failed:', err); });
  };

  // ============================================
  // Boot
  // ============================================
  connectSSE();
})();
