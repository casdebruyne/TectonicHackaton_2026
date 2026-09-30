components.html("""
<div id="b" style="font-size:80px; cursor:pointer; text-align:center; user-select:none;">🎈</div>
<script>
const b = document.getElementById("b");
const audioContext = new (window.AudioContext || window.webkitAudioContext)();

function playPopSound() {
  const now = audioContext.currentTime;
  const osc = audioContext.createOscillator();
  const gain = audioContext.createGain();
  
  osc.connect(gain);
  gain.connect(audioContext.destination);
  
  osc.frequency.setValueAtTime(150, now);
  osc.frequency.exponentialRampToValueAtTime(50, now + 0.1);
  gain.gain.setValueAtTime(0.3, now);
  gain.gain.exponentialRampToValueAtTime(0.01, now + 0.1);
  
  osc.start(now);
  osc.stop(now + 0.1);
}

b.onclick = () => {
  b.textContent = "💥";
  playPopSound();
  setTimeout(() => { b.textContent = "🎈"; }, 800);
};
</script>
""", height=10000)
