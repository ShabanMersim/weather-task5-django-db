function setBusy(b){ b?$("#spinner").removeClass("d-none"):$("#spinner").addClass("d-none"); }
function renderRows(items){
  const $tb=$("#resultsTable tbody"); $tb.empty();
  items.forEach(x=>{
    $tb.append(`<tr>
      <td>${x.name}</td>
      <td>${x.condition}</td>
      <td class="text-center">${x.temp.toFixed(1)}</td>
      <td class="text-center">${x.humidity}</td>
    </tr>`);
  });
}
function renderStats(stats){
  if(!stats){ $("#statsBox").addClass("d-none"); return; }
  $("#statsText").html(`📊 <strong>Най-студен:</strong> ${stats.coldest_city} (${stats.coldest_temp.toFixed(1)} °C)
     &nbsp;|&nbsp; <strong>Средна:</strong> ${stats.avg_temp.toFixed(1)} °C`);
  $("#statsBox").removeClass("d-none");
}
$(function(){
  $("#btnRandom").on("click", function(){
    setBusy(true);
    $.getJSON("/api/refresh_random/").done(d=>{
      renderRows(d.items||[]); renderStats(d.stats||null);
    }).fail(()=>alert("Грешка")).always(()=>setBusy(false));
  });
  $("#btnCheck").on("click", function(){
    const q=$("#cityInput").val().trim(); if(!q){ alert("Въведи град (пример: London,GB)"); return; }
    setBusy(true);
    $.getJSON("/api/refresh_city/", { q }).done(d=>{
      renderRows([d.item]); renderStats(null);
    }).fail((xhr)=>{
      alert((xhr.responseJSON && xhr.responseJSON.error) || "Грешка");
    }).always(()=>setBusy(false));
  });
  $("#btnHistory").on("click", function(){
    const q=$("#cityInput").val().trim(); if(!q){ alert("Въведи град (пример: London,GB)"); return; }
    setBusy(true);
    $.getJSON("/api/history/", { q, limit: 10 }).done(d=>{
      $("#historyCity").text(`${d.city.name} (${d.city.query})`);
      const $tb = $("#historyTable tbody"); $tb.empty();
      d.items.forEach(it=>{
        const dt = new Date(it.fetched_at);
        $tb.append(`<tr>
          <td>${dt.toLocaleString()}</td>
          <td>${it.temp.toFixed(1)} °C</td>
          <td>${it.humidity}</td>
          <td>${it.condition}</td>
        </tr>`);
      });
      $("#historyStats").text(
        `Темп — min: ${d.stats.temp.min.toFixed(1)}°C, max: ${d.stats.temp.max.toFixed(1)}°C, avg: ${d.stats.temp.avg.toFixed(1)}°C; `
        + `Влажност — min: ${d.stats.humidity.min}%, max: ${d.stats.humidity.max}%, avg: ${Math.round(d.stats.humidity.avg)}%.`
      );
      $("#historyBox").removeClass("d-none");
    }).fail((xhr)=>{
      alert((xhr.responseJSON && xhr.responseJSON.error) || "Няма история.");
    }).always(()=> setBusy(false));
  });
});
