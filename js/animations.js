/* =====================================================================
   Deutsch Essay · Wörterbuch — animations
   Hover "text tremble": a barely-perceptible, organic micro-jitter of the
   word, as if the letters flinched at the touch of a brush. NOT a bounce,
   wobble or shake — only ~0.8px random offsets that ease between positions.
   (The brush "reveal" itself is pure CSS — see .wash --reveal in styles.css.)
   ===================================================================== */
(function(){
  const reduce = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  if(reduce) return;

  const AMP = 0.8;      // px — maximum offset
  const ROT = 0.3;      // deg — maximum rotation
  const STEP = 100;     // ms — time between micro-moves
  const DURATION = 930; // ms — tremble for ~1s on hover, then settle (off the tick grid so it lands on 0)
  const live = new Map(); // .de element -> {iv, to}

  const rnd = m => (Math.random()*2 - 1) * m;

  function start(de){
    if(live.has(de)) return;   // already trembling, or already settled during this hover
    de.style.transition = 'transform 110ms ease-out';
    const tick = () => {
      de.style.transform =
        `translate(${rnd(AMP).toFixed(2)}px, ${rnd(AMP*0.7).toFixed(2)}px) rotate(${rnd(ROT).toFixed(2)}deg)`;
    };
    tick();
    const iv = setInterval(tick, STEP);
    // stop after ~1s and let it settle back, even if the cursor stays on the word
    const to = setTimeout(() => { clearInterval(iv); de.style.transform = 'translate(0,0)'; }, DURATION);
    live.set(de, {iv, to});   // entry stays → won't restart until the cursor leaves
  }
  function stop(de){
    const s = live.get(de);
    if(s){ clearInterval(s.iv); clearTimeout(s.to); }
    live.delete(de);          // re-arm for the next hover
    de.style.transform = 'translate(0,0)';
  }

  /* event delegation so it survives list re-renders */
  document.addEventListener('mouseover', e => {
    const word = e.target.closest && e.target.closest('.word');
    if(!word) return;
    const de = word.querySelector('.de');
    if(de) start(de);
  });
  document.addEventListener('mouseout', e => {
    const word = e.target.closest && e.target.closest('.word');
    if(!word) return;
    if(word.contains(e.relatedTarget)) return; // still inside the row
    const de = word.querySelector('.de');
    if(de) stop(de);
  });
})();
