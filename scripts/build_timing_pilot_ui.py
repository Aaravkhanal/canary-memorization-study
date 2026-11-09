#!/usr/bin/env python3
"""Build a standalone, condition-blinded browser interface for the 80-item timing pilot."""

from __future__ import annotations

import argparse
import csv
import html
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def build(rows: list[dict]) -> str:
    if len(rows) != 80:
        raise ValueError(f"timing pilot UI requires 80 rows, found {len(rows)}")
    public = [{"sample_id": row["sample_id"], "prompt": row["prompt"], "generation": row["generation"]}
              for row in rows]
    data = json.dumps(public, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Blinded Timing Pilot</title><style>
:root{{--ink:#172033;--muted:#64748b;--paper:#fff;--bg:#eef2f7;--blue:#174f7d;--line:#cbd5e1}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);font:16px/1.5 system-ui,sans-serif;color:var(--ink)}}
main{{max-width:920px;margin:28px auto;padding:0 18px}} .card{{background:var(--paper);border:1px solid var(--line);border-radius:14px;padding:24px;box-shadow:0 8px 28px #0f172a12}}
.top{{display:flex;justify-content:space-between;gap:16px;align-items:center;margin-bottom:18px}} h1{{font-size:1.35rem;margin:0}} .muted{{color:var(--muted)}}
.progress{{height:9px;background:#dbe4ee;border-radius:99px;overflow:hidden;margin:12px 0 22px}} .bar{{height:100%;background:var(--blue)}}
.text{{white-space:pre-wrap;border:1px solid var(--line);border-radius:10px;padding:16px;margin:9px 0 18px;background:#fafcff}}
.prompt{{font-weight:650}} label{{display:block;font-weight:650;margin:13px 0 6px}} .choices{{display:flex;flex-wrap:wrap;gap:9px}}
button,.choice{{border:1px solid #9fb2c6;background:white;border-radius:9px;padding:10px 15px;cursor:pointer;font:inherit}}
.choice.active{{background:var(--blue);color:white;border-color:var(--blue)}} textarea{{width:100%;min-height:75px;border:1px solid var(--line);border-radius:9px;padding:10px;font:inherit}}
.actions{{display:flex;justify-content:space-between;gap:12px;margin-top:20px}} button.primary{{background:var(--blue);color:white;border-color:var(--blue)}} button:disabled{{opacity:.45;cursor:not-allowed}}
.timer{{font-variant-numeric:tabular-nums;font-weight:700}} dialog{{max-width:600px;border:0;border-radius:14px;padding:25px;box-shadow:0 20px 70px #0005}}
.done{{text-align:center;padding:25px}} code{{background:#e8eef5;padding:2px 5px;border-radius:4px}}
</style></head><body><main><div class="card" id="app"></div></main><dialog id="breakDialog"><h2>Block complete</h2><p>Take at least a five-minute break. Timing is paused. Resume only when rested.</p><p class="timer" id="breakTimer">05:00</p><button id="resume" disabled>Resume next block</button></dialog>
<script>
const items={data}; const KEY='canaryTimingPilotV1';
let state=JSON.parse(localStorage.getItem(KEY)||'null')||{{index:0,answers:{{}}}}; let started=performance.now(),paused=false;
const app=document.getElementById('app'); const save=()=>localStorage.setItem(KEY,JSON.stringify(state));
function tickSeconds(){{if(!paused){{const a=state.answers[items[state.index]?.sample_id];if(a){{a.seconds=(a.seconds||0)+(performance.now()-started)/1000;started=performance.now();save()}}}}}}
setInterval(tickSeconds,1000); document.addEventListener('visibilitychange',()=>{{tickSeconds();paused=document.hidden;started=performance.now()}});
function esc(s){{return String(s).replace(/[&<>"']/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]))}}
function answer(){{const id=items[state.index].sample_id;return state.answers[id]||(state.answers[id]={{pilot_label:'',confidence:'',seconds:0,notes:''}})}}
function choose(field,value){{tickSeconds();answer()[field]=value;save();render()}}
function render(){{started=performance.now();if(state.index>=items.length)return done();const x=items[state.index],a=answer(),block=Math.floor(state.index/20)+1;
app.innerHTML=`<div class="top"><div><h1>Blinded annotation timing pilot</h1><div class="muted">Block ${{block}} of 4 · Item ${{state.index+1}} of 80</div></div><div class="timer">Active time: ${{Math.round(a.seconds)}}s</div></div><div class="progress"><div class="bar" style="width:${{(state.index/80)*100}}%"></div></div><label>Prompt</label><div class="text prompt">${{esc(x.prompt)}}</div><label>Generation</label><div class="text">${{esc(x.generation)}}</div><label>Provisional label</label><div class="choices">${{['V','T','N'].map(v=>`<button class="choice ${{a.pilot_label===v?'active':''}}" onclick="choose('pilot_label','${{v}}')">${{v}}</button>`).join('')}}</div><label>Confidence</label><div class="choices">${{['low','medium','high'].map(v=>`<button class="choice ${{a.confidence===v?'active':''}}" onclick="choose('confidence','${{v}}')">${{v}}</button>`).join('')}}</div><label>Notes (optional)</label><textarea id="notes">${{esc(a.notes)}}</textarea><div class="actions"><button onclick="pauseToggle()">${{paused?'Resume':'Pause timer'}}</button><button class="primary" id="next" ${{!a.pilot_label||!a.confidence?'disabled':''}}>Save and next</button></div>`;
document.getElementById('notes').oninput=e=>{{a.notes=e.target.value;save()}};document.getElementById('next').onclick=next;}}
function pauseToggle(){{tickSeconds();paused=!paused;started=performance.now();render()}}
function next(){{tickSeconds();const a=answer();if(!a.pilot_label||!a.confidence)return;state.index++;save();if(state.index<80&&state.index%20===0)breakNow();else render()}}
function breakNow(){{paused=true;const d=document.getElementById('breakDialog'),b=document.getElementById('resume'),t=document.getElementById('breakTimer');d.showModal();let left=300;b.disabled=true;const h=setInterval(()=>{{left--;t.textContent=String(Math.floor(left/60)).padStart(2,'0')+':'+String(left%60).padStart(2,'0');if(left<=0){{clearInterval(h);b.disabled=false}}}},1000);b.onclick=()=>{{d.close();paused=false;started=performance.now();render()}}}}
function csvCell(v){{const s=String(v??'');return /[",\n]/.test(s)?'"'+s.replaceAll('"','""')+'"':s}}
function exportCsv(){{tickSeconds();const fields=['sample_id','prompt','generation','pilot_label','confidence','seconds','notes'];const lines=[fields.join(',')];for(const x of items){{const a=state.answers[x.sample_id];lines.push([x.sample_id,x.prompt,x.generation,a.pilot_label,a.confidence,Math.round(a.seconds*10)/10,a.notes].map(csvCell).join(','))}}const blob=new Blob([lines.join('\n')+'\n'],{{type:'text/csv'}}),u=URL.createObjectURL(blob),link=document.createElement('a');link.href=u;link.download='timing_pilot_80_completed.csv';link.click();URL.revokeObjectURL(u)}}
function done(){{paused=true;app.innerHTML=`<div class="done"><h1>Pilot complete</h1><p>Export the completed CSV, replace <code>timing_pilot_80.csv</code> with it, and tell Codex “pilot complete.”</p><button class="primary" onclick="exportCsv()">Export completed CSV</button></div>`}}
render();
</script></body></html>"""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path,
                        default=ROOT / "results/confirmatory/annotation_amended/timing_pilot_80.csv")
    parser.add_argument("--output", type=Path,
                        default=ROOT / "results/confirmatory/annotation_amended/timing_pilot_80.html")
    args = parser.parse_args()
    with args.input.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    args.output.write_text(build(rows), encoding="utf-8")
    print(f"[wrote] {args.output}: {len(rows)} blinded items")


if __name__ == "__main__":
    main()
