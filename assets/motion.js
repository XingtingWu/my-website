'use strict';

// A light pointer trail. Keep the native cursor and all hit targets untouched.
(() => {
  const desktopPointer = matchMedia('(min-width: 761px) and (hover: hover) and (pointer: fine)');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  let dispose = () => {};

  function configure() {
    dispose();
    dispose = () => {};
    if (!desktopPointer.matches || reducedMotion.matches) return;

    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    canvas.className = 'pointer-effects';
    canvas.setAttribute('aria-hidden', 'true');
    canvas.dataset.active = 'false';
    document.body.append(canvas);

    // Render one soft brush once, then reuse it for the fading trail.
    const brush = document.createElement('canvas');
    brush.width = brush.height = 96;
    const brushContext = brush.getContext('2d');
    if (!brushContext) { canvas.remove(); return; }
    const ink = brushContext.createRadialGradient(48, 48, 0, 48, 48, 48);
    ink.addColorStop(0, 'rgba(84, 125, 98, .30)');
    ink.addColorStop(.4, 'rgba(108, 143, 114, .14)');
    ink.addColorStop(1, 'rgba(141, 164, 137, 0)');
    brushContext.fillStyle = ink;
    brushContext.fillRect(0, 0, 96, 96);

    const events = new AbortController();
    const listen = (target, name, handler) => target.addEventListener(name, handler, { passive: true, signal: events.signal });
    const pointer = { x: 0, y: 0, drawX: 0, drawY: 0, radius: 10, overLink: false, active: false };
    let particles = [], ripple = null, frame = 0, previousFrame = 0;
    let width = innerWidth, height = innerHeight;

    function clear() {
      cancelAnimationFrame(frame);
      frame = 0;
      particles = [];
      ripple = null;
      pointer.active = false;
      canvas.dataset.active = 'false';
      ctx.clearRect(0, 0, width, height);
    }

    function resize() {
      clear();
      width = innerWidth;
      height = innerHeight;
      const scale = Math.min(devicePixelRatio || 1, 1.5);
      canvas.width = Math.round(width * scale);
      canvas.height = Math.round(height * scale);
      ctx.setTransform(scale, 0, 0, scale, 0, 0);
    }

    function wake() {
      if (!frame) {
        previousFrame = performance.now();
        frame = requestAnimationFrame(paint);
      }
    }

    function paint(now) {
      frame = 0;
      const dt = Math.min(40, Math.max(1, now - previousFrame));
      previousFrame = now;
      ctx.clearRect(0, 0, width, height);
      particles = particles.filter(particle => now - particle.born < 700);
      for (const particle of particles) {
        const age = now - particle.born;
        const life = 1 - age / 700;
        const size = particle.size + age * .008;
        ctx.globalAlpha = life * life * .55;
        ctx.drawImage(brush, particle.x + particle.driftX * age - size, particle.y + particle.driftY * age - size, size * 2, size * 2);
      }
      ctx.globalAlpha = 1;

      if (pointer.active) {
        const follow = 1 - Math.exp(-dt / 45);
        pointer.drawX += (pointer.x - pointer.drawX) * follow;
        pointer.drawY += (pointer.y - pointer.drawY) * follow;
        pointer.radius += ((pointer.overLink ? 19 : 10) - pointer.radius) * follow;
        ctx.globalAlpha = .28;
        ctx.drawImage(brush, pointer.drawX - 32, pointer.drawY - 32, 64, 64);
        ctx.globalAlpha = 1;
        ctx.strokeStyle = pointer.overLink ? 'rgba(68, 104, 78, .58)' : 'rgba(86, 117, 93, .36)';
        ctx.lineWidth = .8;
        ctx.beginPath();
        ctx.arc(pointer.drawX, pointer.drawY, pointer.radius, 0, Math.PI * 2);
        ctx.stroke();
      }

      if (ripple) {
        const progress = Math.min(1, (now - ripple.born) / 360);
        ctx.strokeStyle = `rgba(78, 115, 89, ${.25 * (1 - progress)})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.arc(ripple.x, ripple.y, 7 + 25 * progress, 0, Math.PI * 2);
        ctx.stroke();
        if (progress === 1) ripple = null;
      }

      const following = pointer.active && (Math.hypot(pointer.x - pointer.drawX, pointer.y - pointer.drawY) > .1 || Math.abs(pointer.radius - (pointer.overLink ? 19 : 10)) > .1);
      // Stop painting when still; leave the final ring in place until the next move.
      if (particles.length || ripple || following) frame = requestAnimationFrame(paint);
    }

    function move(event) {
      if (event.pointerType !== 'mouse') return;
      const target = event.target instanceof Element ? event.target : null;
      if (event.buttons || target?.closest('input, textarea, select, [contenteditable="true"], dialog')) { clear(); return; }
      const x = event.clientX, y = event.clientY;
      const fromX = pointer.active ? pointer.x : x;
      const fromY = pointer.active ? pointer.y : y;
      if (!pointer.active) { pointer.drawX = x; pointer.drawY = y; }
      const distance = Math.hypot(x - fromX, y - fromY);
      const steps = Math.min(6, Math.max(1, Math.ceil(distance / 15)));
      const born = performance.now();
      for (let i = 1; i <= steps; i++) {
        const progress = i / steps;
        particles.push({ x: fromX + (x - fromX) * progress, y: fromY + (y - fromY) * progress, born, size: 22 + Math.min(distance, 80) * .16, driftX: (Math.random() - .5) * .012, driftY: (Math.random() - .5) * .012 });
      }
      if (particles.length > 72) particles.splice(0, particles.length - 72);
      pointer.x = x;
      pointer.y = y;
      pointer.active = true;
      pointer.overLink = Boolean(target?.closest('a[href], button:not(:disabled), [role="button"], [role="tab"]'));
      canvas.dataset.active = 'true';
      canvas.dataset.mode = pointer.overLink ? 'link' : 'default';
      wake();
    }

    listen(document, 'pointermove', move);
    listen(document, 'pointerdown', event => {
      if (event.pointerType === 'mouse' && pointer.active) {
        ripple = { x: event.clientX, y: event.clientY, born: performance.now() };
        wake();
      }
    });
    listen(document, 'pointerout', event => { if (!event.relatedTarget) clear(); });
    listen(window, 'blur', clear);
    listen(window, 'scroll', clear);
    listen(window, 'resize', resize);
    listen(document, 'visibilitychange', () => { if (document.hidden) clear(); });
    resize();
    dispose = () => { events.abort(); clear(); canvas.remove(); };
  }

  desktopPointer.addEventListener('change', configure);
  reducedMotion.addEventListener('change', configure);
  configure();
})();
