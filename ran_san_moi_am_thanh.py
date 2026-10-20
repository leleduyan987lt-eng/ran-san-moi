import streamlit as st

st.set_page_config(page_title="Rắn săn mồi", page_icon="🐍", layout="centered")

st.title("🐍 Rắn săn mồi")
st.write("Ăn táo để ghi điểm, đừng đâm vào tường hoặc cắn phải chính mình!")

html = r'''<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
  * { box-sizing: border-box; }
  body { margin: 0; padding: 0 0 8px; font-family: Arial, sans-serif; color: #eef2ff; background: transparent; }
  .wrap { max-width: 540px; margin: 0 auto; }
  .top { display: flex; justify-content: space-between; align-items: center; gap: 10px; margin: 4px 0 12px; }
  .scorebox { background: #172033; border: 1px solid #2a3853; border-radius: 12px; padding: 10px 15px; flex: 1; text-align: center; }
  .label { display:block; color:#9fb0cc; font-size:12px; margin-bottom:4px; }
  .value { font-size:23px; font-weight:700; }
  .gamebox { position: relative; width: 100%; }
  canvas { display:block; width:100%; height:auto; border: 2px solid #334155; border-radius: 12px; background: #0b1220; outline: none; touch-action: none; }
  .status { min-height: 34px; padding: 9px 4px 4px; text-align:center; color:#dbeafe; font-size:14px; }
  .actions { display:flex; justify-content:center; gap:9px; flex-wrap:wrap; margin: 8px 0 12px; }
  button { border:0; border-radius:10px; padding:10px 16px; color:white; background:#2563eb; font-size:14px; font-weight:700; cursor:pointer; }
  button:hover { filter: brightness(1.12); }
  button.secondary { background:#334155; }
  .touch { width: 180px; margin: 0 auto; display:grid; grid-template-columns: repeat(3, 1fr); gap:7px; }
  .touch button { padding:11px 0; font-size:19px; background:#263449; border:1px solid #3b4b63; touch-action: manipulation; }
  .touch .empty { visibility:hidden; }
  .help { color:#9caec8; text-align:center; font-size:12px; line-height:1.55; margin-top:12px; }
  @media (max-width:420px) { .value {font-size:20px;} .scorebox {padding:8px 5px;} button {padding:10px 12px;} }
</style>
</head>
<body>
<div class="wrap">
  <div class="top">
    <div class="scorebox"><span class="label">ĐIỂM</span><span class="value" id="score">0</span></div>
    <div class="scorebox"><span class="label">KỶ LỤC VÁN NÀY</span><span class="value" id="best">0</span></div>
  </div>
  <div class="gamebox">
    <canvas id="board" width="480" height="480" tabindex="0" aria-label="Bàn chơi rắn săn mồi"></canvas>
  </div>
  <div class="status" id="status">Bấm “Bật âm thanh” để nghe hiệu ứng và giọng đọc “Game Over” khi thua. Bấm “Bắt đầu” để chơi.</div>
  <div class="actions">
    <button id="start">▶ Bắt đầu</button>
    <button id="pause" class="secondary">⏸ Tạm dừng</button>
    <button id="restart" class="secondary">↻ Chơi lại</button>
    <button id="sound" class="secondary" aria-pressed="false">🔇 Bật âm thanh</button>
  </div>
  <div class="touch" aria-label="Nút điều khiển">
    <button class="empty" tabindex="-1">·</button><button data-dir="up" aria-label="Lên">⬆️</button><button class="empty" tabindex="-1">·</button>
    <button data-dir="left" aria-label="Trái">⬅️</button><button data-dir="down" aria-label="Xuống">⬇️</button><button data-dir="right" aria-label="Phải">➡️</button>
  </div>
  <div class="help">Máy tính: dùng ↑ ↓ ← → hoặc W A S D. Điện thoại/máy tính bảng: dùng các nút mũi tên.<br>Ăn táo 🍎 để được 10 điểm mỗi quả. Nhấn Space để tạm dừng. Bấm “Bật âm thanh” để bật hiệu ứng khi ăn táo và giọng đọc “Game Over” khi thua.</div>
</div>
<script>
(() => {
  const canvas = document.getElementById('board');
  const ctx = canvas.getContext('2d');
  const scoreEl = document.getElementById('score');
  const bestEl = document.getElementById('best');
  const statusEl = document.getElementById('status');
  const startBtn = document.getElementById('start');
  const pauseBtn = document.getElementById('pause');
  const restartBtn = document.getElementById('restart');
  const soundBtn = document.getElementById('sound');
  const CELLS = 20, SIZE = canvas.width / CELLS;
  let snake, food, dir, nextDir, score, started, paused, over, lastStep, lastTime;
  // Âm thanh mặc định tắt để trình duyệt không chặn phát tự động.
  // Người chơi bấm nút “Bật âm thanh” để mở tiếng và nghe thử ngay.
  let soundOn = false;
  let audioCtx = null;
  const bgMusic = new Audio("https://raw.githubusercontent.com/leleduyan987lt-eng/ran-san-moi/main/wtf.mp3");
  bgMusic.loop = true;
  bgMusic.volume = 0.35;
  // Tạo âm thanh ngay trong trình duyệt, không cần tải file MP3.
  // AudioContext được khởi tạo trong thao tác bấm nút để tránh chính sách chặn autoplay.
  async function getAudioContext() {
    if (!soundOn) return null;
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (!AudioContextClass) return null;
      if (!audioCtx) audioCtx = new AudioContextClass();
      if (audioCtx.state !== 'running') await audioCtx.resume();
      return audioCtx.state === 'running' ? audioCtx : null;
    } catch (e) {
      return null;
    }
  }
  async function beep(freq, duration, type='sine', volume=0.11, delay=0) {
    const ac = await getAudioContext();
    if (!ac || !soundOn) return;
    const startAt = ac.currentTime + delay;
    const oscillator = ac.createOscillator();
    const gain = ac.createGain();
    oscillator.type = type;
    oscillator.frequency.setValueAtTime(freq, startAt);
    gain.gain.setValueAtTime(0.0001, startAt);
    gain.gain.exponentialRampToValueAtTime(volume, startAt + 0.015);
    gain.gain.exponentialRampToValueAtTime(0.0001, startAt + duration);
    oscillator.connect(gain);
    gain.connect(ac.destination);
    oscillator.start(startAt);
    oscillator.stop(startAt + duration + 0.025);
  }
  function soundEat() {
    // Hai nốt sáng, dễ nhận ra khi rắn ăn táo.
    beep(784, 0.10, 'sine', 0.13, 0);
    beep(1046, 0.15, 'sine', 0.13, 0.09);
  }
  function soundStart() {
    beep(523, 0.10, 'sine', 0.11, 0);
    beep(784, 0.13, 'sine', 0.11, 0.10);
  }
  function soundGameOver() {
    // Hiệu ứng ba nốt trầm dần khi thua.
    beep(330, 0.14, 'triangle', 0.12, 0);
    beep(247, 0.18, 'triangle', 0.12, 0.14);
    beep(165, 0.27, 'triangle', 0.12, 0.32);

    // Đọc thành tiếng "Game Over!" nếu trình duyệt hỗ trợ giọng đọc.
    // Nếu không hỗ trợ, hiệu ứng ba nốt phía trên vẫn phát bình thường.
    if (soundOn && 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window) {
      try {
        window.speechSynthesis.cancel();
        const message = new SpeechSynthesisUtterance('Game Over!');
        message.lang = 'en-US';
        message.rate = 0.88;
        message.pitch = 0.7;
        message.volume = 1;
        window.speechSynthesis.speak(message);
      } catch (e) {
        // Bỏ qua lỗi giọng đọc; âm báo bằng nốt vẫn hoạt động.
      }
    }
  }
  function soundWin() {
    beep(523, 0.12, 'sine', 0.12, 0);
    beep(659, 0.12, 'sine', 0.12, 0.12);
    beep(784, 0.18, 'sine', 0.12, 0.24);
    beep(1047, 0.24, 'sine', 0.12, 0.42);
  }

  function randomFood() {
    let p;
    do { p = {x: Math.floor(Math.random()*CELLS), y: Math.floor(Math.random()*CELLS)}; }
    while (snake.some(s => s.x === p.x && s.y === p.y));
    return p;
  }
  function reset() {
    snake = [{x:9,y:10},{x:8,y:10},{x:7,y:10}];
    dir = {x:1,y:0}; nextDir = {x:1,y:0};
    score = 0; started = false; paused = false; over = false;
    food = randomFood(); lastStep = 0; lastTime = 0;
    scoreEl.textContent = '0'; bestEl.textContent = '0';
    statusEl.textContent = 'Bấm “Bật âm thanh” để nghe hiệu ứng và giọng đọc “Game Over” khi thua. Bấm “Bắt đầu” để chơi.';
    startBtn.textContent = '▶ Bắt đầu'; pauseBtn.textContent = '⏸ Tạm dừng';
    soundBtn.textContent = soundOn ? '🔊 Âm thanh: Bật' : '🔇 Bật âm thanh';
    soundBtn.setAttribute('aria-pressed', String(soundOn));
    draw();
  }
  function setDirection(x,y) {
    if (x === -dir.x && y === -dir.y) return;
    nextDir = {x,y};
    if (!started && !over) { /* Chọn hướng trước khi bắt đầu cũng được */ }
  }
  function move() {
    dir = nextDir;
    const head = {x:snake[0].x + dir.x, y:snake[0].y + dir.y};
    const eating = head.x === food.x && head.y === food.y;
    const body = eating ? snake : snake.slice(0, -1);
    if (head.x < 0 || head.x >= CELLS || head.y < 0 || head.y >= CELLS || body.some(p => p.x === head.x && p.y === head.y)) {
      over = true; started = false;
      bgMusic.pause();
      bgMusic.currentTime = 0;
      bgMusic.pause();
      bgMusic.currentTime = 0;
      soundGameOver();
      statusEl.textContent = `💥 Game Over! Bạn đạt ${score} điểm. Bấm “Chơi lại” để thử lần nữa.`;
      startBtn.textContent = '▶ Bắt đầu lại';
      return;
    }
    snake.unshift(head);
    if (eating) {
      score += 10; scoreEl.textContent = String(score); bestEl.textContent = String(score);
      soundEat();
      if (snake.length >= CELLS*CELLS) {
        over = true; started = false; soundWin(); statusEl.textContent = `🏆 Tuyệt vời! Bạn đã lấp đầy bàn chơi với ${score} điểm!`; draw(); return;
      }
      food = randomFood();
    } else snake.pop();
    draw();
  }
  function roundedRect(x,y,w,h,r) {
    ctx.beginPath(); ctx.roundRect(x,y,w,h,r); ctx.fill();
  }
  function draw() {
    ctx.fillStyle = '#0b1220'; ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.strokeStyle = 'rgba(148,163,184,0.09)'; ctx.lineWidth = 1;
    for (let i=1;i<CELLS;i++) { ctx.beginPath();ctx.moveTo(i*SIZE,0);ctx.lineTo(i*SIZE,canvas.height);ctx.stroke();ctx.beginPath();ctx.moveTo(0,i*SIZE);ctx.lineTo(canvas.width,i*SIZE);ctx.stroke(); }
    // Táo
    const fx = food.x*SIZE + SIZE/2, fy = food.y*SIZE + SIZE/2;
    ctx.font = `${SIZE*0.8}px serif`; ctx.textAlign='center'; ctx.textBaseline='middle'; ctx.fillText('🍎',fx,fy+1);
    // Rắn
    snake.forEach((p,i) => {
      const pad = i===0 ? 2 : 3;
      ctx.fillStyle = i===0 ? '#a3e635' : `hsl(${103 - Math.min(i,18)*1.8}, 62%, ${48 - Math.min(i,18)*0.45}%)`;
      roundedRect(p.x*SIZE+pad,p.y*SIZE+pad,SIZE-pad*2,SIZE-pad*2, i===0 ? 7 : 5);
      if (i===0) {
        ctx.fillStyle='#172033';
        let e1,e2;
        if(dir.x===1){e1=[p.x*SIZE+SIZE*.68,p.y*SIZE+SIZE*.32];e2=[p.x*SIZE+SIZE*.68,p.y*SIZE+SIZE*.68];}
        else if(dir.x===-1){e1=[p.x*SIZE+SIZE*.32,p.y*SIZE+SIZE*.32];e2=[p.x*SIZE+SIZE*.32,p.y*SIZE+SIZE*.68];}
        else if(dir.y===-1){e1=[p.x*SIZE+SIZE*.32,p.y*SIZE+SIZE*.32];e2=[p.x*SIZE+SIZE*.68,p.y*SIZE+SIZE*.32];}
        else {e1=[p.x*SIZE+SIZE*.32,p.y*SIZE+SIZE*.68];e2=[p.x*SIZE+SIZE*.68,p.y*SIZE+SIZE*.68];}
        [e1,e2].forEach(e=>{ctx.beginPath();ctx.arc(e[0],e[1],2.1,0,Math.PI*2);ctx.fill();});
      }
    });
    if (paused) overlay('TẠM DỪNG', 'Nhấn Space hoặc “Tiếp tục” để chơi');
    else if (!started && !over) overlay('SẴN SÀNG?', 'Bấm Bắt đầu để chơi');
    else if (over && !statusEl.textContent.includes('🏆')) overlay('GAME OVER', 'Bấm Chơi lại để thử lần nữa');
  }
  function overlay(title, subtitle) {
    ctx.fillStyle='rgba(3,7,18,0.68)';ctx.fillRect(0,0,canvas.width,canvas.height);
    ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillStyle='#f8fafc';ctx.font='bold 30px Arial';ctx.fillText(title,canvas.width/2,canvas.height/2-14);
    ctx.fillStyle='#cbd5e1';ctx.font='15px Arial';ctx.fillText(subtitle,canvas.width/2,canvas.height/2+20);
  }
  function startGame() {
    if (over) reset();
    started = true; paused = false;
    bgMusic.currentTime = 0;
    bgMusic.play().catch(() => {});
    soundStart();
    startBtn.textContent='▶ Đang chơi';
    statusEl.textContent='Đang chơi! Ăn táo 🍎 và tránh tường cùng thân rắn.';
    canvas.focus(); draw();
  }
  function togglePause() {
    if (over) return;
    if (!started) { startGame(); return; }
    paused = !paused;
    beep(paused ? 392 : 587, 0.09, 'sine', 0.03);
    pauseBtn.textContent = paused ? '▶ Tiếp tục' : '⏸ Tạm dừng';
    statusEl.textContent = paused ? '⏸ Đã tạm dừng. Nhấn “Tiếp tục” hoặc Space.' : 'Đang chơi! Ăn táo 🍎 và tránh tường cùng thân rắn.';
    draw();
  }
  document.addEventListener('keydown', e => {
    const k=e.key.toLowerCase();
    const keys=['arrowup','arrowdown','arrowleft','arrowright','w','a','s','d',' '];
    if(keys.includes(k)) e.preventDefault();
    if(k==='arrowup'||k==='w') setDirection(0,-1);
    else if(k==='arrowdown'||k==='s') setDirection(0,1);
    else if(k==='arrowleft'||k==='a') setDirection(-1,0);
    else if(k==='arrowright'||k==='d') setDirection(1,0);
    else if(k===' ') togglePause();
  });
  document.querySelectorAll('[data-dir]').forEach(b=>b.addEventListener('click',()=>{
    const d=b.dataset.dir;
    if(d==='up') setDirection(0,-1); if(d==='down') setDirection(0,1);
    if(d==='left') setDirection(-1,0); if(d==='right') setDirection(1,0);
    canvas.focus();
  }));
  startBtn.addEventListener('click', startGame);
  pauseBtn.addEventListener('click', togglePause);
  restartBtn.addEventListener('click', reset);
  soundBtn.addEventListener('click', async () => {
    if (soundOn) {
      soundOn = false;
      soundBtn.textContent = '🔇 Bật âm thanh';
      soundBtn.setAttribute('aria-pressed', 'false');
      statusEl.textContent = 'Đã tắt âm thanh. Bấm nút này lần nữa để bật lại.';
      return;
    }
    soundOn = true;
    soundBtn.textContent = '🔊 Âm thanh: Bật';
    soundBtn.setAttribute('aria-pressed', 'true');
    const ac = await getAudioContext();
    if (ac) {
      soundStart();
      statusEl.textContent = '🔊 Âm thanh đã bật! Bạn sẽ nghe tiếng khi rắn ăn táo.';
    } else {
      statusEl.textContent = 'Không mở được âm thanh. Hãy kiểm tra âm lượng Windows/Chrome rồi tải lại trang.';
    }
  });
  function loop(t) {
    if (started && !paused && !over) {
      if (!lastStep) lastStep=t;
      const delay=Math.max(65, 145 - score*0.6);
      if (t-lastStep >= delay) { move(); lastStep=t; }
    } else { lastStep=0; }
    requestAnimationFrame(loop);
  }
  reset(); requestAnimationFrame(loop);
})();
</script>
</body>
</html>'''

st.iframe(html, height=900, tab_index=0, alt="Game rắn săn mồi có âm thanh Game Over, không có nhạc nền")


with st.expander("❓ Nếu game không nhận phím mũi tên"):
    st.write("Bấm chuột một lần lên bàn chơi, sau đó dùng phím mũi tên hoặc W/A/S/D. Bạn cũng có thể bấm các nút mũi tên bên dưới bàn chơi.")

st.caption("Chúc bạn đạt điểm cao! 🐍 Trên máy tính, dùng phím mũi tên hoặc WASD; trên điện thoại, bấm các nút điều khiển.")
