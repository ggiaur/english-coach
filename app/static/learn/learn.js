(function () {
  var NAV = [
    ["/learn/", "Kezdőlap"], ["/learn/john9.html", "János 9"], ["/learn/cards.html", "Kártyák"],
    ["/learn/book.html", "Tankönyv"], ["/progress", "Haladás"], ["/", "Tutor"]
  ];
  var L = window.Learn = {};

  L.el = function (tag, attrs, text) {
    var n = document.createElement(tag);
    for (var k in (attrs || {})) n.setAttribute(k, attrs[k]);
    if (text !== undefined && text !== null) n.textContent = text;
    return n;
  };

  L.nav = function () {
    var h = L.el("header", { "class": "site" });
    var nav = L.el("nav", { "aria-label": "Menü" });
    var here = location.pathname.replace(/\/index\.html$/, "/");
    NAV.forEach(function (it) {
      var a = L.el("a", { href: it[0] }, it[1]);
      if (it[0] === here || (here === "/learn" && it[0] === "/learn/")) a.setAttribute("aria-current", "page");
      nav.appendChild(a);
    });
    h.appendChild(nav);
    document.body.insertBefore(h, document.body.firstChild);
  };

  L.json = function (name) {
    return fetch("/learn/data/" + name).then(function (r) {
      if (!r.ok) throw new Error(name);
      return r.json();
    });
  };

  L.img = function (id, alt) {
    if (!id) return null;
    var i = L.el("img", { src: "/learn/img/" + id + ".svg", alt: alt || "", loading: "lazy" });
    return i;
  };

  // ---- audio: local Piper through /tts, browser voice as fallback ----
  var player = null, ttsOk = null, token = 0;
  var RATES = { slow: 0.6, medium: 0.85, natural: 1 };

  function stop() {
    token++;
    if (player) { try { player.pause(); } catch (e) {} player = null; }
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  }
  L.stop = stop;

  function viaBrowser(text, speed, my) {
    return new Promise(function (resolve) {
      if (!("speechSynthesis" in window)) return resolve();
      var u = new SpeechSynthesisUtterance(text);
      u.lang = "en-US"; u.rate = RATES[speed] || 1;
      u.onend = u.onerror = function () { resolve(); };
      window.speechSynthesis.speak(u);
    });
  }
  function viaServer(text, speed, my) {
    return fetch("/tts?text=" + encodeURIComponent(text) + "&speed=" + speed).then(function (r) {
      if (!r.ok) throw new Error("tts " + r.status);
      return r.blob();
    }).then(function (b) {
      return new Promise(function (resolve, reject) {
        if (my !== token) return resolve();
        var a = new Audio(URL.createObjectURL(b));
        player = a;
        a.onended = function () { resolve(); };
        a.onerror = function () { reject(new Error("audio")); };
        a.play().catch(reject);
      });
    });
  }
  L.speak = function (text, speed) {
    stop();
    var my = token;
    speed = speed || "natural";
    if (ttsOk === false) return viaBrowser(text, speed, my);
    return viaServer(text, speed, my).then(function () { ttsOk = true; }).catch(function () {
      if (ttsOk === null) ttsOk = false;
      if (my === token) return viaBrowser(text, speed, my);
    });
  };
  // four speeds: very slow, very slow, medium, natural
  L.speakFour = function (text) {
    stop();
    var my = token;
    var order = ["slow", "slow", "medium", "natural"];
    var p = Promise.resolve();
    order.forEach(function (sp) {
      p = p.then(function () {
        if (my !== token) return;
        var q = ttsOk === false ? viaBrowser(text, sp, my) :
          viaServer(text, sp, my).then(function () { ttsOk = true; }).catch(function () {
            if (ttsOk === null) ttsOk = false;
            if (my === token) return viaBrowser(text, sp, my);
          });
        return q.then(function () {
          return new Promise(function (r) { setTimeout(r, sp === "natural" ? 0 : 900); });
        });
      });
    });
    return p;
  };

  L.audioButtons = function (text) {
    var row = L.el("span", { "class": "row" });
    var b1 = L.el("button", { "class": "play", type: "button", "aria-label": "Lejátszás" }, "▶");
    b1.onclick = function () { L.speak(text, "natural"); };
    var b2 = L.el("button", { "class": "ghost", type: "button", "aria-label": "Lassan" }, "🐢 lassan");
    b2.onclick = function () { L.speak(text, "slow"); };
    var b3 = L.el("button", { "class": "ghost", type: "button", "aria-label": "Négy sebesség" }, "4 sebesség");
    b3.onclick = function () { L.speakFour(text); };
    row.appendChild(b1); row.appendChild(b2); row.appendChild(b3);
    return row;
  };

  document.addEventListener("DOMContentLoaded", L.nav);
})();
