// app/web/app.js
const $ = (id)=>document.getElementById(id);
const API = (path)=>`${location.origin.replace(/\/$/,'')}${path}`;

$("btnPrice").onclick = async ()=>{
  const code = $("code").value.trim();
  const res = await fetch(API(`/api/quotes/${encodeURIComponent(code)}`));
  $("priceBox").textContent = JSON.stringify(await res.json(), null, 2);
};

$("btnOrder").onclick = async ()=>{
  const body = {
    code: $("code2").value.trim(),
    qty: parseInt($("qty").value,10),
    side: $("side").value
  };
  const res = await fetch(API(`/api/orders/market`), {method:"POST", headers:{'Content-Type':'application/json'}, body:JSON.stringify(body)});
  $("orderBox").textContent = JSON.stringify(await res.json(), null, 2);
};

$("btnReco").onclick = async ()=>{
  const codes = $("codes").value.split(",").map(s=>s.trim()).filter(Boolean);
  const qs = new URLSearchParams();
  codes.forEach(c=>qs.append("codes", c));
  const res = await fetch(API(`/api/reco/topn?${qs.toString()}`));
  $("recoBox").textContent = JSON.stringify(await res.json(), null, 2);
};
