(function() {
    var container = document.getElementById("report-data");
    if (!container) return;

    var reportId = container.dataset.reportId;
    var totalEngines = parseInt(container.dataset.enginesTotal, 10);
    var completed = 0;
    // Verdict band edges come from app/config.py via the template, so colours
    // always agree with the verdict text the server computed.
    var bands = (container.dataset.bands || "30,45,55,80").split(",").map(Number);

    function bandIndex(score) {
        for (var i = 0; i < bands.length; i++) {
            if (score <= bands[i]) return i;
        }
        return bands.length;
    }

    function getScoreColor(score) {
        return ["var(--c-clean)", "var(--c-low)", "var(--c-warn)", "var(--c-danger)", "var(--c-slop)"][bandIndex(score)];
    }

    function getBarColor(score) {
        if (score < 0.4) return "var(--c-clean)";
        if (score < 0.65) return "var(--c-warn)";
        return "var(--c-slop)";
    }

    function getVerdictClass(score) {
        return ["verdict-clean", "verdict-low", "verdict-suspicious", "verdict-likely", "verdict-slop"][bandIndex(score)];
    }

    function updateGauge(overall) {
        var fill = document.getElementById("gauge-fill");
        var num = document.getElementById("gauge-number");
        var dashLen = (overall / 100) * 534;
        fill.style.strokeDasharray = dashLen + " 534";
        fill.style.stroke = getScoreColor(overall);
        num.textContent = overall.toFixed(1);
        num.style.color = getScoreColor(overall);
    }

    function updateVerdict(data) {
        var el = document.getElementById("verdict-text");
        el.textContent = data.overall_verdict;
        el.className = "verdict-text " + getVerdictClass(data.overall_score);

        var fc = document.getElementById("flagged-count");
        if (data.done) {
            fc.innerHTML = "<strong>" + data.engines_flagged + "</strong> / " + data.engines_total + " engines flagged this content";
        } else {
            fc.innerHTML = "<strong>" + data.engines_done + "</strong> / " + data.engines_total + " engines completed";
        }
    }

    function setDone() {
        var status = document.getElementById("scan-status");
        status.innerHTML = '<span class="status-dot done"></span><span class="status-label">Complete</span>';
        document.getElementById("progress-text").textContent = totalEngines + " / " + totalEngines;
        document.body.classList.add("scan-complete");
    }

    function updateEngineRow(data) {
        var row = document.getElementById("row-" + data.key);
        if (!row) return;

        row.classList.remove("engine-row-pending");
        row.classList.add("engine-row-done");

        var badge = document.getElementById("verdict-" + data.key);
        badge.className = "verdict-badge verdict-badge-" + data.verdict;
        badge.textContent = data.verdict.toUpperCase();

        var bar = document.getElementById("bar-" + data.key);
        var pct = (data.score * 100).toFixed(1);
        bar.style.width = pct + "%";
        bar.style.background = getBarColor(data.score);

        var scoreEl = document.getElementById("score-" + data.key);
        scoreEl.textContent = pct + "%";

        var details = document.getElementById("details-" + data.key);
        details.textContent = data.details;
    }

    var evtSource = new EventSource("/api/stream/" + reportId);

    evtSource.onmessage = function(event) {
        var data = JSON.parse(event.data);

        if (data.done) {
            evtSource.close();
            setDone();
            fetch("/api/report/" + reportId)
                .then(function(r) { return r.json(); })
                .then(function(report) {
                    updateGauge(report.overall_score);
                    var el = document.getElementById("verdict-text");
                    el.textContent = report.overall_verdict;
                    el.className = "verdict-text " + getVerdictClass(report.overall_score);
                    var fc = document.getElementById("flagged-count");
                    fc.innerHTML = "<strong>" + report.engines_flagged + "</strong> / " + report.engines_total + " engines flagged this content";
                });
            return;
        }

        completed++;
        updateEngineRow(data);
        updateGauge(data.overall_score);
        updateVerdict(data);
        document.getElementById("progress-text").textContent = completed + " / " + totalEngines;
    };

    evtSource.onerror = function() {
        evtSource.close();
        setDone();
    };

    document.getElementById("copy-btn").addEventListener("click", function() {
        navigator.clipboard.writeText(window.location.href);
        this.querySelector("svg").style.display = "none";
        var orig = this.childNodes[this.childNodes.length - 1];
        var oldText = orig.textContent;
        orig.textContent = " Copied!";
        var btn = this;
        setTimeout(function() {
            btn.querySelector("svg").style.display = "";
            orig.textContent = oldText;
        }, 2000);
    });

    // ---- Site fingerprints (URL reports only) ----
    var siteCard = document.getElementById("site-check");
    if (siteCard) {
        fetch("/api/scan/site", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({url: siteCard.dataset.url, include_text: false})
        })
            .then(function(r) { return r.ok ? r.json() : null; })
            .then(function(d) {
                if (!d || !d.site) return;
                var s = d.site;
                var title = siteCard.querySelector(".site-verdict");
                title.textContent = s.verdict;
                siteCard.classList.toggle("site-found", s.builders.length > 0);
                var list = siteCard.querySelector(".site-evidence");
                list.innerHTML = "";
                s.builders.forEach(function(b) {
                    b.evidence.forEach(function(ev) {
                        var li = document.createElement("li");
                        li.textContent = b.name + ": " + ev;
                        list.appendChild(li);
                    });
                });
                if (s.generator) {
                    var li = document.createElement("li");
                    li.textContent = "Generator tag: " + s.generator;
                    list.appendChild(li);
                }
                siteCard.hidden = false;
            })
            .catch(function() {});
    }
})();
