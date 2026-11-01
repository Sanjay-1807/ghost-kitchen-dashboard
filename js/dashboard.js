(function () {
  'use strict';
  var D = window.DASH;
  var css = getComputedStyle(document.documentElement);
  var C = {
    before: css.getPropertyValue('--before').trim(),
    after: css.getPropertyValue('--after').trim(),
    grid: css.getPropertyValue('--grid').trim(),
    text: css.getPropertyValue('--text').trim(),
    text2: css.getPropertyValue('--text-2').trim(),
    muted: css.getPropertyValue('--muted').trim(),
    accent: css.getPropertyValue('--accent').trim()
  };

  Chart.defaults.font.family = '"Segoe UI", system-ui, -apple-system, Roboto, Arial, sans-serif';
  Chart.defaults.color = C.text2;
  Chart.defaults.borderColor = C.grid;

  var money = function (v) { return '$' + v.toFixed(2); };
  var moneyK = function (v) { return '$' + Math.round(v).toLocaleString('en-US'); };
  var pct = function (v) { return v.toFixed(1) + '%'; };
  var min = function (v) { return v.toFixed(2) + ' min'; };
  var num2 = function (v) { return v.toFixed(2); };
  var int = function (v) { return String(Math.round(v)); };

  // ---------------------------------------------------------------- KPI tiles
  var KPIS = [
    { name: 'Order Accuracy Rate', key: 'accuracy', fmt: pct, better: 'up', unit: ' pts' },
    { name: 'Avg Profit per Order (after refunds)', key: 'profit_after_refunds', fmt: money, better: 'up', unit: '' },
    { name: 'Peak-Hour Staffing Ratio (orders per staff)', key: 'peak_staffing_ratio', fmt: num2, better: 'down', unit: '' },
    { name: 'Prep-Time Variance (min past quote)', key: 'prep_variance', fmt: min, better: 'down', unit: ' min' },
    { name: 'Customer Satisfaction Rating', key: 'rating', fmt: num2, better: 'up', unit: ' stars' },
    { name: 'Refund Rate', key: 'refund_rate', fmt: pct, better: 'down', unit: ' pts' }
  ];
  var grid = document.getElementById('kpiGrid');
  KPIS.forEach(function (k) {
    var b = D.before.kpi[k.key], a = D.after.kpi[k.key];
    var diff = a - b;
    var improved = (k.better === 'up' && diff > 0) || (k.better === 'down' && diff < 0);
    var mag = Math.abs(diff);
    var diffTxt = k.key === 'profit_after_refunds' ? '$' + mag.toFixed(2) : (k.key === 'accuracy' || k.key === 'refund_rate' ? mag.toFixed(1) : mag.toFixed(2)) + k.unit;
    var rel = b !== 0 ? Math.round(Math.abs(diff / b) * 100) : 0;
    var el = document.createElement('div');
    el.className = 'kpi';
    el.innerHTML =
      '<p class="name">' + k.name + '</p>' +
      '<div class="vals"><span class="b">' + k.fmt(b) + '</span><span class="arrow" aria-hidden="true">&rarr;</span><span class="a">' + k.fmt(a) + '</span></div>' +
      '<div class="tags"><span class="tb">Before</span><span class="ta">After</span></div>' +
      '<div class="delta ' + (improved ? 'good' : 'flat') + '">' +
      (improved ? (diff > 0 ? '&#9650; ' : '&#9660; ') + diffTxt + ' (' + rel + '%) &middot; better' : 'No change') + '</div>';
    grid.appendChild(el);
  });

  // ---------------------------------------------------------------- charts
  var SPECS = {
    brand_accuracy: { title: 'Order accuracy by brand', labels: D.brands, fmt: pct, max: 100, axis: function (v) { return v + '%'; } },
    peak_accuracy: { title: 'Order accuracy: non-peak vs peak hours', labels: ['Non-peak hours', 'Peak hours'], fmt: pct, max: 100, axis: function (v) { return v + '%'; } },
    peak_variance: { title: 'Prep delay past quoted time: non-peak vs peak', labels: ['Non-peak hours', 'Peak hours'], fmt: min, axis: function (v) { return v + ' min'; } },
    hour_ratio: { title: 'Orders waiting per staff member, by hour', labels: D.before.hour_labels, fmt: num2, threshold: 2, noLabels: true, axis: function (v) { return v; } },
    hour_staff: { title: 'Staff scheduled, by hour', labels: D.before.hour_labels, fmt: int, noLabels: true, step: 1, axis: function (v) { return v; } },
    brand_rating: { title: 'Average customer rating by brand', labels: D.brands, fmt: num2, max: 5, axis: function (v) { return v; } },
    refund_platform: { title: 'Refund rate by platform', labels: D.platforms, fmt: pct, axis: function (v) { return v + '%'; } },
    refund_loss_brand: { title: 'Money lost to refunds by brand (full year)', labels: D.brands, fmt: moneyK, axis: function (v) { return '$' + v; } },
    profit_after_refunds_platform: { title: 'Avg profit per order after refunds, by platform', labels: D.platforms, fmt: money, axis: function (v) { return '$' + v; } }
  };

  // draws the value above each bar (selective direct labels)
  var valueLabels = {
    id: 'valueLabels',
    afterDatasetsDraw: function (chart, args, opts) {
      if (!opts || !opts.fmt) return;
      var ctx = chart.ctx;
      ctx.save();
      ctx.fillStyle = C.text;
      ctx.font = '600 12px "Segoe UI", system-ui, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'bottom';
      chart.getDatasetMeta(0).data.forEach(function (bar, i) {
        var v = chart.data.datasets[0].data[i];
        ctx.fillText(opts.fmt(v), bar.x, bar.y - 5);
      });
      ctx.restore();
    }
  };
  // dashed threshold line (e.g. staffing ratio target of 2)
  var thresholdLine = {
    id: 'thresholdLine',
    afterDatasetsDraw: function (chart, args, opts) {
      if (!opts || opts.value == null) return;
      var y = chart.scales.y.getPixelForValue(opts.value);
      var a = chart.chartArea;
      var ctx = chart.ctx;
      ctx.save();
      ctx.strokeStyle = C.accent;
      ctx.lineWidth = 1.5;
      ctx.setLineDash([6, 4]);
      ctx.beginPath(); ctx.moveTo(a.left, y); ctx.lineTo(a.right, y); ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = C.accent;
      ctx.font = '600 11px "Segoe UI", system-ui, sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText('Alert above ' + opts.value, a.left + 4, y - 6);
      ctx.restore();
    }
  };

  function niceMax(vals) {
    var m = Math.max.apply(null, vals) * 1.15;
    var raw = m / 5;
    var mag = Math.pow(10, Math.floor(Math.log10(raw)));
    var step = [1, 2, 2.5, 5, 10].map(function (f) { return f * mag; }).filter(function (s) { return s >= raw; })[0];
    return Math.ceil(m / step) * step;
  }

  function panel(spec, which, data, yMax) {
    var wrap = document.createElement('div');
    wrap.className = 'panel';
    wrap.innerHTML = '<div class="panel-head"><h3>' + spec.title + '</h3><span class="badge ' + which + '">' +
      (which === 'before' ? 'BEFORE &middot; DATASET 1' : 'AFTER &middot; DATASET 2') + '</span></div><div class="chart"><canvas></canvas></div>';
    var canvas = wrap.querySelector('canvas');
    canvas.setAttribute('role', 'img');
    canvas.setAttribute('aria-label', spec.title + ', ' + (which === 'before' ? 'before' : 'after') + ': ' +
      spec.labels.map(function (l, i) { return l + ' ' + spec.fmt(data[i]); }).join(', '));
    setTimeout(function () {
      new Chart(canvas, {
        type: 'bar',
        data: { labels: spec.labels, datasets: [{ data: data, backgroundColor: C[which], borderRadius: { topLeft: 4, topRight: 4 }, borderSkipped: 'bottom', maxBarThickness: 64, categoryPercentage: 0.7, barPercentage: 0.9 }] },
        options: {
          responsive: true, maintainAspectRatio: false, animation: { duration: 500 },
          layout: { padding: { top: 18 } },
          plugins: {
            legend: { display: false },
            tooltip: { callbacks: { label: function (c) { return (which === 'before' ? 'Before: ' : 'After: ') + spec.fmt(c.raw); } } },
            valueLabels: spec.noLabels ? false : { fmt: spec.fmt },
            thresholdLine: spec.threshold ? { value: spec.threshold } : false
          },
          scales: {
            y: { beginAtZero: true, max: yMax, grid: { color: C.grid }, border: { display: false }, ticks: { color: C.muted, callback: spec.axis, stepSize: spec.step, maxTicksLimit: 7 } },
            x: { grid: { display: false }, ticks: { color: C.text2, autoSkip: false, maxRotation: 0, font: { size: spec.labels.length > 6 ? 10 : 12 } } }
          }
        },
        plugins: [valueLabels, thresholdLine]
      });
    }, 0);
    return wrap;
  }

  document.querySelectorAll('.pair[data-chart]').forEach(function (holder) {
    var key = holder.getAttribute('data-chart');
    var spec = SPECS[key];
    var b = D.before[key], a = D.after[key];
    var yMax = spec.max || niceMax(b.concat(a).concat(spec.threshold ? [spec.threshold] : []));
    holder.appendChild(panel(spec, 'before', b, yMax));
    holder.appendChild(panel(spec, 'after', a, yMax));
    // accessible data table
    var foot = document.createElement('div');
    foot.className = 'pair-foot';
    var rows = spec.labels.map(function (l, i) {
      return '<tr><td>' + l + '</td><td class="n">' + spec.fmt(b[i]) + '</td><td class="n">' + spec.fmt(a[i]) + '</td></tr>';
    }).join('');
    foot.innerHTML = '<details class="data"><summary>Show data table</summary><table><thead><tr><th></th><th class="n">Before</th><th class="n">After</th></tr></thead><tbody>' + rows + '</tbody></table></details>';
    holder.appendChild(foot);
  });
})();
