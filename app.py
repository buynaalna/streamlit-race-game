import streamlit as st
import streamlit.components.v1 as components


GAME_SETTINGS = {
    "title": "Drag Race Simulator",
    "laps": 3,
    "controls": ["WASD", "arrow keys", "mouse drag", "touch drag"],
}


def make_game_description(settings):
    """Build the instructions from the game's Python settings."""
    control_text = []
    for control in settings["controls"]:
        control_text.append(control)

    if settings["laps"] == 1:
        lap_text = "one lap"
    else:
        lap_text = f"{settings['laps']} laps"

    return f"Use {' / '.join(control_text)}. Complete {lap_text} before the computer!"


st.set_page_config(page_title="Drag Race Simulator", page_icon="🏎️", layout="wide")

st.title(f"🏎️ {GAME_SETTINGS['title']}")
st.caption(make_game_description(GAME_SETTINGS))

GAME = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
<style>
  * { box-sizing: border-box; }
  body { margin: 0; background: #101820; color: white; font-family: system-ui, sans-serif; overflow: hidden; }
  #wrap { width: 100%; max-width: 1000px; margin: auto; position: relative; }
  canvas { width: 100%; height: auto; display: block; border-radius: 18px; touch-action: none; }
  #hud { position: absolute; inset: 14px 16px auto 16px; display: flex; justify-content: space-between; pointer-events: none; }
  .panel { background: #071018dd; border: 1px solid #ffffff42; border-radius: 12px; padding: 9px 14px; font-weight: 750; box-shadow: 0 5px 18px #0007; }
  #message { position: absolute; left: 50%; top: 50%; transform: translate(-50%,-50%); text-align: center; background: #071018ee; padding: 22px 32px; border-radius: 18px; border: 2px solid #fff6; min-width: 290px; }
  #message h2 { margin: 0 0 8px; font-size: 30px; }
  button { border: 0; border-radius: 10px; padding: 10px 18px; font-size: 17px; font-weight: 800; background: #ffcc00; color: #151515; cursor: pointer; }
  #help { text-align: center; padding: 10px; color: #c9d1d9; font-size: 14px; }
</style>
</head>
<body>
<div id="wrap">
  <canvas id="game" width="960" height="560"></canvas>
  <div id="hud">
    <div class="panel">YOU: <span id="playerLap">0</span>/3 laps</div>
    <div class="panel">Speed: <span id="speed">0</span></div>
    <div class="panel">CPU: <span id="cpuLap">0</span>/3 laps</div>
  </div>
  <div id="message">
    <h2>🏁 Ready to race?</h2>
    <p>Drive with the keyboard or drag on the track.</p>
    <button id="start">START RACE</button>
  </div>
</div>
<div id="help">⌨️ WASD / arrow keys &nbsp;•&nbsp; 🖱️ Hold and drag &nbsp;•&nbsp; 📱 Touch and drag</div>

<script>
const canvas = document.getElementById('game');
const ctx = canvas.getContext('2d');
const W = canvas.width, H = canvas.height;
const CX = W/2, CY = H/2 + 12;
const OUT_RX = 410, OUT_RY = 220, IN_RX = 245, IN_RY = 90;
const MID_RX = (OUT_RX + IN_RX) / 2, MID_RY = (OUT_RY + IN_RY) / 2;
const LAPS_TO_WIN = 3;

const player = { x: CX + MID_RX, y: CY, angle: Math.PI/2, speed: 0, laps: 0, progress: 0, lastTheta: 0 };
const cpu = { x: 0, y: 0, angle: 0, laps: 0, theta: -0.22 };
const keys = {};
let playing = false, dragging = false, target = null, winner = null, lastTime = 0;

function reset() {
  Object.assign(player, {x: CX + MID_RX, y: CY, angle: Math.PI/2, speed: 0, laps: 0, progress: 0, lastTheta: 0});
  Object.assign(cpu, {laps: 0, theta: -0.22});
  winner = null; playing = true; target = null; lastTime = performance.now();
  document.getElementById('message').style.display = 'none';
}

function onRoad(x, y) {
  const dx = x-CX, dy = y-CY;
  const outer = dx*dx/(OUT_RX*OUT_RX) + dy*dy/(OUT_RY*OUT_RY);
  const inner = dx*dx/(IN_RX*IN_RX) + dy*dy/(IN_RY*IN_RY);
  return outer <= 1 && inner >= 1;
}

function pointerPosition(e) {
  const r = canvas.getBoundingClientRect();
  const p = e.touches ? e.touches[0] : e;
  return {x: (p.clientX-r.left)*W/r.width, y: (p.clientY-r.top)*H/r.height};
}

canvas.addEventListener('pointerdown', e => { dragging = true; target = pointerPosition(e); canvas.setPointerCapture(e.pointerId); });
canvas.addEventListener('pointermove', e => { if (dragging) target = pointerPosition(e); });
canvas.addEventListener('pointerup', () => { dragging = false; target = null; });
canvas.addEventListener('touchstart', e => { dragging = true; target = pointerPosition(e); e.preventDefault(); }, {passive:false});
canvas.addEventListener('touchmove', e => { target = pointerPosition(e); e.preventDefault(); }, {passive:false});
canvas.addEventListener('touchend', () => { dragging = false; target = null; });

window.addEventListener('keydown', e => {
  keys[e.key.toLowerCase()] = true;
  if (["arrowup","arrowdown","arrowleft","arrowright"," "].includes(e.key.toLowerCase())) e.preventDefault();
});
window.addEventListener('keyup', e => keys[e.key.toLowerCase()] = false);
document.getElementById('start').onclick = reset;

function update(dt) {
  if (!playing || winner) return;
  const up = keys['arrowup'] || keys['w'];
  const down = keys['arrowdown'] || keys['s'];
  const left = keys['arrowleft'] || keys['a'];
  const right = keys['arrowright'] || keys['d'];

  if (dragging && target) {
    const dx = target.x-player.x, dy = target.y-player.y;
    const distance = Math.hypot(dx,dy);
    player.angle = Math.atan2(dy,dx);
    player.speed = Math.min(330, distance*3.2);
  } else {
    if (up) player.speed += 250*dt;
    if (down) player.speed -= 280*dt;
    if (!up && !down) player.speed *= Math.pow(0.965, dt*60);
    const steering = Math.min(1, Math.abs(player.speed)/100);
    if (left) player.angle -= 2.5*dt*steering*Math.sign(player.speed || 1);
    if (right) player.angle += 2.5*dt*steering*Math.sign(player.speed || 1);
    player.speed = Math.max(-100, Math.min(310, player.speed));
  }

  if (!onRoad(player.x,player.y)) player.speed *= Math.pow(0.93,dt*60);
  player.x += Math.cos(player.angle)*player.speed*dt;
  player.y += Math.sin(player.angle)*player.speed*dt;
  player.x = Math.max(20,Math.min(W-20,player.x));
  player.y = Math.max(20,Math.min(H-20,player.y));

  const theta = Math.atan2((player.y-CY)/MID_RY,(player.x-CX)/MID_RX);
  let delta = theta-player.lastTheta;
  if (delta < -Math.PI) delta += Math.PI*2;
  if (delta > Math.PI) delta -= Math.PI*2;
  if (onRoad(player.x,player.y) && delta > -0.08) player.progress += Math.max(0,delta);
  player.lastTheta = theta;
  player.laps = Math.min(LAPS_TO_WIN,Math.floor(player.progress/(Math.PI*2)));

  cpu.theta += 0.57*dt;
  cpu.laps = Math.min(LAPS_TO_WIN,Math.floor((cpu.theta+0.22)/(Math.PI*2)));
  cpu.x = CX+MID_RX*Math.cos(cpu.theta);
  cpu.y = CY+MID_RY*Math.sin(cpu.theta);
  cpu.angle = Math.atan2(MID_RY*Math.cos(cpu.theta),-MID_RX*Math.sin(cpu.theta));

  if (player.laps >= LAPS_TO_WIN) endRace('YOU WIN! 🎉');
  else if (cpu.laps >= LAPS_TO_WIN) endRace('CPU WINS! 🤖');
}

function endRace(text) {
  winner = text; playing = false;
  const box = document.getElementById('message');
  box.innerHTML = `<h2>${text}</h2><p>Great race! Try again?</p><button id="again">RACE AGAIN</button>`;
  box.style.display = 'block';
  document.getElementById('again').onclick = reset;
}

function drawCar(car,color,label) {
  ctx.save(); ctx.translate(car.x,car.y); ctx.rotate(car.angle);
  ctx.shadowColor='#0009'; ctx.shadowBlur=8;
  ctx.fillStyle=color; ctx.fillRect(-18,-11,36,22);
  ctx.fillStyle='#bde7ff'; ctx.fillRect(-5,-8,12,16);
  ctx.fillStyle='#111'; ctx.fillRect(-14,-14,9,4); ctx.fillRect(6,-14,9,4); ctx.fillRect(-14,10,9,4); ctx.fillRect(6,10,9,4);
  ctx.restore();
  ctx.fillStyle='white'; ctx.font='bold 13px system-ui'; ctx.textAlign='center'; ctx.fillText(label,car.x,car.y-20);
}

function draw() {
  ctx.fillStyle='#19743c'; ctx.fillRect(0,0,W,H);
  ctx.fillStyle='#3f454c'; ctx.beginPath(); ctx.ellipse(CX,CY,OUT_RX,OUT_RY,0,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='#fff'; ctx.lineWidth=5; ctx.setLineDash([18,18]); ctx.beginPath(); ctx.ellipse(CX,CY,MID_RX,MID_RY,0,0,Math.PI*2); ctx.stroke(); ctx.setLineDash([]);
  ctx.fillStyle='#238a48'; ctx.beginPath(); ctx.ellipse(CX,CY,IN_RX,IN_RY,0,0,Math.PI*2); ctx.fill();
  ctx.strokeStyle='#eaeaea'; ctx.lineWidth=5; ctx.beginPath(); ctx.ellipse(CX,CY,OUT_RX,OUT_RY,0,0,Math.PI*2); ctx.stroke(); ctx.beginPath(); ctx.ellipse(CX,CY,IN_RX,IN_RY,0,0,Math.PI*2); ctx.stroke();

  const fx=CX+IN_RX, fw=OUT_RX-IN_RX;
  for(let i=0;i<6;i++) for(let j=0;j<2;j++) { ctx.fillStyle=(i+j)%2?'#fff':'#111'; ctx.fillRect(fx+i*fw/6,CY-13+j*13,fw/6,13); }

  ctx.fillStyle='#ffffff18'; ctx.font='bold 48px system-ui'; ctx.textAlign='center'; ctx.fillText('RACE',CX,CY+16);
  if (dragging && target) { ctx.strokeStyle='#ffcc00'; ctx.lineWidth=4; ctx.beginPath(); ctx.moveTo(player.x,player.y); ctx.lineTo(target.x,target.y); ctx.stroke(); ctx.beginPath(); ctx.arc(target.x,target.y,13,0,Math.PI*2); ctx.stroke(); }
  drawCar(cpu,'#ff3b30','CPU'); drawCar(player,'#1687ff','YOU');

  document.getElementById('playerLap').textContent=player.laps;
  document.getElementById('cpuLap').textContent=cpu.laps;
  document.getElementById('speed').textContent=Math.round(Math.abs(player.speed));
}

function loop(t) {
  const dt=Math.min(0.033,(t-lastTime)/1000 || 0); lastTime=t;
  update(dt); draw(); requestAnimationFrame(loop);
}
draw(); requestAnimationFrame(loop);
</script>
</body>
</html>
"""

components.html(GAME, height=660, scrolling=False)

with st.expander("How the game works"):
    st.write(
        "The blue car is the player and the red car is controlled by the computer. "
        "Stay on the gray track, complete three clockwise laps, and reach the finish first."
    )
