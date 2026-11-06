(function () {
  var KEY = "englishCoachProgress.v1";
  function load() { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) { return {}; } }
  function save(s) { try { localStorage.setItem(KEY, JSON.stringify(s)); } catch (e) {} }
  var state = load();
  var data;

  function el(tag, attrs, text) {
    var n = document.createElement(tag);
    for (var k in (attrs || {})) n.setAttribute(k, attrs[k]);
    if (text) n.textContent = text;
    return n;
  }
  function link(url, text) {
    var a = el("a", { href: url, target: "_blank", rel: "noopener" }, text);
    return a;
  }

  function update() {
    var boxes = document.querySelectorAll("#days input[type=checkbox]");
    var done = 0;
    boxes.forEach(function (b) { if (b.checked) done++; });
    var pct = boxes.length ? Math.round(done * 100 / boxes.length) : 0;
    document.getElementById("barfill").style.width = pct + "%";
    document.getElementById("pct").textContent = done + " / " + boxes.length + " kész (" + pct + "%)";
  }

  function render() {
    document.getElementById("week").textContent = "Hét: " + data.week;
    var songById = {};
    data.songs.forEach(function (s) { songById[s.id] = s; });
    var days = document.getElementById("days");
    data.days.forEach(function (d) {
      var box = el("div", { "class": "day" });
      box.appendChild(el("h3", {}, d.day + " – " + d.title));
      var tasks = d.items.slice();
      var song = d.song ? songById[d.song] : null;
      tasks.forEach(function (t, i) { addCheck(box, d.id + "-" + i, t); });
      if (song) {
        var row = addCheck(box, d.id + "-song", "Dal (10'): " + song.title + " – ");
        row.appendChild(link(song.url, "megnyitás"));
      }
      days.appendChild(box);
    });
    var sl = document.getElementById("songs");
    data.songs.forEach(function (s) {
      var li = el("li");
      li.appendChild(link(s.url, s.title + " – " + s.artist));
      li.appendChild(document.createTextNode(" (" + s.official + ") · "));
      li.appendChild(link(s.search, "keresés, ha a videó nem elérhető"));
      sl.appendChild(li);
    });
    var rl = document.getElementById("resources");
    data.resources.forEach(function (r) {
      var li = el("li"); li.appendChild(link(r.url, r.title)); rl.appendChild(li);
    });
    document.getElementById("repo").href = data.repo;
    update();
  }

  function addCheck(box, id, text) {
    var label = el("label");
    var cb = el("input", { type: "checkbox" });
    cb.checked = !!state[id];
    cb.addEventListener("change", function () { state[id] = cb.checked; save(state); update(); });
    label.appendChild(cb);
    var span = el("span", {}, text);
    label.appendChild(span);
    box.appendChild(label);
    return span;
  }

  document.getElementById("f-date").value = new Date().toISOString().slice(0, 10);
  document.getElementById("logform").addEventListener("submit", function (e) {
    e.preventDefault();
    var v = function (id) { return document.getElementById(id).value; };
    document.getElementById("record").value =
      "SESSION RECORD\ndate: " + v("f-date") +
      "\ntrack: \nlesson: \nminutes_actual: " + v("f-min") +
      "\ntime_of_day: " + v("f-tod") +
      "\nfreshness_1_5: " + v("f-fresh") +
      "\ndaily_speaking: " + v("f-speak") +
      "\nnew_items_taught: []\nsaid_correctly_first_try_today: []\nsaid_correctly_after_repair: []\npending: []\nerrors_seen: []\nnext_priority: []\n";
  });
  document.getElementById("copy").addEventListener("click", function () {
    var t = document.getElementById("record");
    t.select();
    try { document.execCommand("copy"); } catch (e) {}
  });
  document.getElementById("reset").addEventListener("click", function () {
    if (confirm("Biztosan törlöd az összes pipát?")) {
      state = {}; save(state);
      document.querySelectorAll("#days input[type=checkbox]").forEach(function (b) { b.checked = false; });
      update();
    }
  });

  fetch("/progress/data.json").then(function (r) { return r.json(); }).then(function (d) { data = d; render(); })
    .catch(function () { document.getElementById("week").textContent = "Az adatok nem tölthetők be."; });
})();
