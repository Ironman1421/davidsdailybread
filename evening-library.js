(function () {
  "use strict";
  var section = document.body.getAttribute("data-library-section");
  var grid = document.getElementById("libraryGrid");
  var input = document.getElementById("librarySearch");
  var count = document.getElementById("libraryCount");
  var message = document.getElementById("libraryMessage");
  var cards = [];

  function element(name, className, text) {
    var node = document.createElement(name);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function safeUrl(value) {
    try {
      var url = new URL(value);
      return url.protocol === "https:" && !url.username && !url.password ? url.href : "";
    } catch (error) {
      return "";
    }
  }

  function dateLabel(value) {
    var parts = String(value || "").split("-");
    if (parts.length !== 3) return "Recent edition";
    var date = new Date(Date.UTC(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2])));
    return date.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "UTC" });
  }

  function chip(text, extraClass) {
    return element("span", "chip" + (extraClass ? " " + extraClass : ""), text);
  }

  function toolCard(item) {
    var href = safeUrl(item.url);
    if (!href) return null;
    var card = element("article", "card");
    card.setAttribute("data-library-card", "");
    var link = element("a"); link.href = href;
    link.appendChild(element("div", "date", dateLabel(item.date)));
    link.appendChild(element("h2", "", String(item.name || "")));
    var chips = element("div", "chips");
    chips.appendChild(chip(String(item.cost || ""), "cost"));
    chips.appendChild(chip(String(item.kind || ""), ""));
    chips.appendChild(chip(String(item.seen || ""), "seen"));
    link.appendChild(chips);
    link.appendChild(element("p", "", String(item.blurb || "")));
    card.appendChild(link);
    return card;
  }

  function workflowCard(item) {
    var href = safeUrl(item.url);
    if (!href) return null;
    var card = element("article", "card");
    card.setAttribute("data-library-card", "");
    var link = element("a"); link.href = href;
    link.appendChild(element("div", "date", dateLabel(item.date)));
    link.appendChild(element("h2", "", String(item.title || "")));
    var chips = element("div", "chips");
    chips.appendChild(chip(String(item.time || ""), "seen"));
    if (item.seen) chips.appendChild(chip(String(item.seen), "seen"));
    link.appendChild(chips);
    link.appendChild(element("p", "", String(item.dek || "").replace(/<\/?b>/g, "")));
    var needs = element("div", "needs");
    needs.appendChild(element("b", "", "You need"));
    (Array.isArray(item.needs) ? item.needs : []).forEach(function (value) {
      needs.appendChild(element("span", "", String(value)));
    });
    link.appendChild(needs);
    card.appendChild(link);
    return card;
  }

  function updateSearch() {
    var query = input.value.trim().toLowerCase();
    var visible = 0;
    cards.forEach(function (card) {
      var show = !query || card.textContent.toLowerCase().indexOf(query) !== -1;
      card.hidden = !show;
      if (show) visible += 1;
    });
    count.textContent = visible + (visible === 1 ? " item" : " items");
    message.hidden = visible !== 0;
    if (!visible) message.textContent = "Nothing here matches that search yet.";
  }

  fetch("/evening-catalog.json", { cache: "no-store", credentials: "omit" })
    .then(function (response) { if (!response.ok) throw new Error("catalog unavailable"); return response.json(); })
    .then(function (data) {
      if (!data || data.version !== 1 || !Array.isArray(data[section])) throw new Error("catalog invalid");
      data[section].forEach(function (item) {
        var card = section === "tools" ? toolCard(item) : workflowCard(item);
        if (card) { cards.push(card); grid.appendChild(card); }
      });
      input.disabled = false;
      updateSearch();
    })
    .catch(function () {
      message.hidden = false;
      message.textContent = "The evening library could not be loaded. Tonight's edition and RSS are still available.";
      count.textContent = "Unavailable";
    });
  input.addEventListener("input", updateSearch);
})();
