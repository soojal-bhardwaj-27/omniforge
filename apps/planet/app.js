// Planet Interactive Experience Controller

const THEMES = {
  green: {
    bgStart: '#1ebb5a',
    bgEnd: '#148b41',
    accent: '#22c55e',
    glow: 'rgba(34, 197, 94, 0.45)',
    name: 'Electric Green'
  },
  cyan: {
    bgStart: '#0ea5e9',
    bgEnd: '#0369a1',
    accent: '#00f0ff',
    glow: 'rgba(0, 240, 255, 0.45)',
    name: 'Neon Cyan'
  },
  orange: {
    bgStart: '#ea580c',
    bgEnd: '#9a3412',
    accent: '#ff6b00',
    glow: 'rgba(255, 107, 0, 0.45)',
    name: 'Solar Orange'
  },
  red: {
    bgStart: '#e11d48',
    bgEnd: '#881337',
    accent: '#ff1e46',
    glow: 'rgba(255, 30, 70, 0.45)',
    name: 'Inferno Red'
  }
};

let currentTheme = 'green';
let currentSize = '43';

// 1. Color Palette Theme Switcher
function setTheme(themeKey) {
  if (!THEMES[themeKey]) return;
  currentTheme = themeKey;
  const t = THEMES[themeKey];

  // Update CSS custom properties for instant smooth transition
  document.documentElement.style.setProperty('--theme-bg-start', t.bgStart);
  document.documentElement.style.setProperty('--theme-bg-end', t.bgEnd);
  document.documentElement.style.setProperty('--theme-accent', t.accent);
  document.documentElement.style.setProperty('--theme-glow', t.glow);

  // Update SVG sneaker accent fills
  const shoeAccents = document.querySelectorAll('.shoe-accent');
  shoeAccents.forEach(el => {
    el.setAttribute('fill', t.accent);
  });

  // Update active color swatch badge
  document.querySelectorAll('.color-swatch').forEach(sw => sw.classList.remove('active'));
  const activeSwatch = document.querySelector(`.swatch-${themeKey}`);
  if (activeSwatch) activeSwatch.classList.add('active');

  // Update modal label
  const modalColor = document.getElementById('modal-color-name');
  if (modalColor) modalColor.textContent = t.name;

  // Trigger burst of splash particles
  createParticleBurst(t.accent);
}

// 2. Interactive Size Selector
function selectSize(element, sizeVal) {
  document.querySelectorAll('.size-pill').forEach(pill => pill.classList.remove('active'));
  element.classList.add('active');
  currentSize = sizeVal;

  const modalSize = document.getElementById('modal-size-val');
  if (modalSize) modalSize.textContent = `EU ${sizeVal}`;
}

// 3. 3D Mouse Parallax Tilt Physics on Sneaker
const sneakerWrapper = document.getElementById('sneaker-wrapper');
const jumpText = document.getElementById('jump-bg');

window.addEventListener('mousemove', (e) => {
  const { innerWidth, innerHeight } = window;
  const x = (e.clientX / innerWidth) - 0.5;
  const y = (e.clientY / innerHeight) - 0.5;

  // Smooth 3D tilt calculation
  const rotateX = y * -20;
  const rotateY = x * 25;
  const translateY = y * 15;

  if (sneakerWrapper) {
    sneakerWrapper.style.transform = `
      translate(${x * 30}px, ${translateY}px) 
      rotateX(${rotateX}deg) 
      rotateY(${rotateY}deg) 
      rotate(-20deg)
    `;
  }

  if (jumpText) {
    jumpText.style.transform = `
      translate(${x * -20}px, ${y * -15}px)
      perspective(1000px) rotateX(${4 + y * 5}deg)
    `;
  }
});

// 4. Order Modal Flow
function openOrderModal() {
  const modal = document.getElementById('order-modal');
  modal.classList.add('open');
}

function closeOrderModal(e) {
  const modal = document.getElementById('order-modal');
  modal.classList.remove('open');
}

function confirmOrder() {
  const modal = document.getElementById('order-modal');
  const card = modal.querySelector('.order-modal-card');
  card.innerHTML = `
    <div style="font-size: 3.5rem; margin-bottom: 16px;">🎉</div>
    <h2 style="font-size: 1.8rem; font-weight: 800; margin-bottom: 12px;">Order Placed!</h2>
    <p style="color: rgba(255,255,255,0.8); line-height: 1.6; margin-bottom: 24px;">
      Your pair of <strong>[planet] Air High</strong> in <strong>${THEMES[currentTheme].name}</strong> (Size ${currentSize}) is being prepared for express delivery.
    </p>
    <button class="btn-confirm-order" onclick="location.reload()">Continue Browsing</button>
  `;
}

function showCatalogToast() {
  alert("Exploring full [planet] 2026 Collection — 14 New Colorways dropping this Friday!");
}

// 5. Dynamic Ink Splatter Particles Canvas
const canvas = document.getElementById('particles-canvas');
const ctx = canvas.getContext('2d');
let particles = [];

function resizeCanvas() {
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
}
window.addEventListener('resize', resizeCanvas);
resizeCanvas();

class Particle {
  constructor(x, y, color) {
    this.x = x;
    this.y = y;
    this.radius = Math.random() * 4 + 1.5;
    this.vx = (Math.random() - 0.5) * 6;
    this.vy = (Math.random() - 0.5) * 6;
    this.alpha = 0.7;
    this.color = color || '#000000';
    this.decay = Math.random() * 0.01 + 0.005;
  }

  update() {
    this.x += this.vx;
    this.y += this.vy;
    this.alpha -= this.decay;
  }

  draw() {
    ctx.save();
    ctx.globalAlpha = Math.max(0, this.alpha);
    ctx.fillStyle = this.color;
    ctx.beginPath();
    ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  }
}

// Seed permanent artistic ink dots behind shoe
const staticSplatterDots = [];
function seedStaticSplatters() {
  const centerX = window.innerWidth * 0.52;
  const centerY = window.innerHeight * 0.5;
  for (let i = 0; i < 45; i++) {
    const angle = Math.random() * Math.PI * 2;
    const dist = Math.random() * 260 + 60;
    staticSplatterDots.push({
      x: centerX + Math.cos(angle) * dist,
      y: centerY + Math.sin(angle) * dist,
      radius: Math.random() * 3.5 + 1,
      alpha: Math.random() * 0.35 + 0.15,
      color: '#000000'
    });
  }
}
seedStaticSplatters();

function createParticleBurst(color) {
  const centerX = window.innerWidth * 0.52;
  const centerY = window.innerHeight * 0.5;
  for (let i = 0; i < 30; i++) {
    particles.push(new Particle(centerX, centerY, color));
  }
}

function animateParticles() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Draw static splatter backdrop dots
  staticSplatterDots.forEach(dot => {
    ctx.save();
    ctx.globalAlpha = dot.alpha;
    ctx.fillStyle = dot.color;
    ctx.beginPath();
    ctx.arc(dot.x, dot.y, dot.radius, 0, Math.PI * 2);
    ctx.fill();
    ctx.restore();
  });

  // Animate dynamic burst particles
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i];
    p.update();
    p.draw();
    if (p.alpha <= 0) {
      particles.splice(i, 1);
    }
  }

  requestAnimationFrame(animateParticles);
}
animateParticles();
