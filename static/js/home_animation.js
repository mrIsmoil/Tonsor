/**
 * MASTERPIECE NEURAL SILK - High-Fidelity 3D-Depth Background
 * Developed for Tonsor - Licensed to Premium Barbershops.
 * Features multi-layer parallax, stellar dust, and variable-blur rendering.
 */

class NeuralSilkEngine {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d', { alpha: true });
        
        this.strands = [];
        this.particles = [];
        this.mouse = { x: null, y: null, radius: 350 };
        this.layers = 3; // Parallax depth layers
        
        this.init();
        this.animate();
        
        window.addEventListener('resize', () => this.handleResize());
        window.addEventListener('mousemove', (e) => this.handleMouseMove(e));
        window.addEventListener('mouseout', () => this.handleMouseOut());
    }

    init() {
        this.handleResize();
        this.createNeuralEcosystem();
    }

    handleResize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
        this.createNeuralEcosystem();
    }

    handleMouseMove(e) {
        this.mouse.x = e.clientX;
        this.mouse.y = e.clientY;
    }

    handleMouseOut() {
        this.mouse.x = null;
        this.mouse.y = null;
    }

    createNeuralEcosystem() {
        this.strands = [];
        this.particles = [];

        // Balanced strand generation across layers
        for (let i = 0; i < 35; i++) {
            const layer = i % this.layers;
            this.strands.push(new NeuralStrand(this.canvas, layer));
        }

        // High-density micro-particles (Stellar Dust)
        for (let i = 0; i < 180; i++) {
            const layer = i % this.layers;
            this.particles.push(new StellarParticle(this.canvas, layer));
        }
    }

    animate() {
        // Clear with a very slight persistence for motion blur
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        
        // Draw in layer order (Background to Foreground)
        for (let l = 0; l < this.layers; l++) {
            // Apply layer-specific blur for depth-of-field
            // Note: Heavy blur can be expensive; we use transparency + shadow for more stable perf
            
            for (let particle of this.particles) {
                if (particle.layer === l) {
                    particle.update(this.mouse);
                    particle.draw(this.ctx);
                }
            }

            for (let strand of this.strands) {
                if (strand.layer === l) {
                    strand.update(this.mouse);
                    strand.draw(this.ctx);
                }
            }
        }
        
        requestAnimationFrame(() => this.animate());
    }
}

class NeuralStrand {
    constructor(canvas, layer) {
        this.canvas = canvas;
        this.layer = layer; // 0 = back, 1 = mid, 2 = front
        this.reset();
    }

    reset() {
        this.x = Math.random() * this.canvas.width;
        this.y = Math.random() * this.canvas.height;
        this.points = [];
        
        // Layer-specific physical properties
        const speedMult = (this.layer + 1) * 0.4;
        this.segments = Math.floor(Math.random() * 20 + 20);
        this.thickness = (this.layer + 1) * 1.2;
        this.velocity = (Math.random() * 0.5 + 0.2) * speedMult;
        this.angle = Math.random() * Math.PI * 2;
        this.curve = (Math.random() - 0.5) * 0.008;
        this.baseOpacity = (this.layer + 1) * 0.12;

        for (let i = 0; i < this.segments; i++) {
            this.points.push({ x: this.x, y: this.y });
        }
    }

    update(mouse) {
        this.angle += this.curve;
        this.x += Math.cos(this.angle) * this.velocity;
        this.y += Math.sin(this.angle) * this.velocity;

        // Neural Mouse Interactivity (Ripple Physics)
        if (mouse.x !== null && mouse.y !== null) {
            let dx = mouse.x - this.x;
            let dy = mouse.y - this.y;
            let dist = Math.sqrt(dx * dx + dy * dy);
            
            if (dist < mouse.radius) {
                let angleToMouse = Math.atan2(dy, dx);
                let force = (mouse.radius - dist) / mouse.radius;
                
                // Repel and Curve
                this.angle += (angleToMouse - this.angle) * force * 0.02 * (this.layer + 1);
                this.velocity = Math.min(this.velocity + force * 0.5, 3.5);
            } else {
                if (this.velocity > 0.4) this.velocity *= 0.985;
            }
        }

        // Smooth bounds reset
        if (this.x < -300 || this.x > this.canvas.width + 300 || 
            this.y < -300 || this.y > this.canvas.height + 300) {
            this.reset();
        }

        this.points.unshift({ x: this.x, y: this.y });
        if (this.points.length > this.segments) this.points.pop();
    }

    draw(ctx) {
        ctx.beginPath();
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';
        
        // Multi-layered light rendering
        for (let i = 1; i < this.points.length - 2; i++) {
            const p1 = this.points[i];
            const p2 = this.points[i + 1];
            
            const midX = (p1.x + p2.x) / 2;
            const midY = (p1.y + p2.y) / 2;
            
            // Tapered opacity and width based on distance from head
            const progression = (1 - i / this.points.length);
            const alpha = progression * this.baseOpacity;
            const width = progression * this.thickness;

            ctx.lineWidth = width;
            ctx.strokeStyle = `rgba(255, 255, 255, ${alpha})`;
            
            ctx.quadraticCurveTo(p1.x, p1.y, midX, midY);
        }
        ctx.stroke();
        
        // Head Glow for closest strands
        if (this.layer === 2) {
            ctx.beginPath();
            const headGlow = ctx.createRadialGradient(this.x, this.y, 0, this.x, this.y, 15);
            headGlow.addColorStop(0, `rgba(255,255,255,${this.baseOpacity * 1.5})`);
            headGlow.addColorStop(1, 'rgba(255,255,255,0)');
            ctx.fillStyle = headGlow;
            ctx.arc(this.x, this.y, 15, 0, Math.PI * 2);
            ctx.fill();
        }
    }
}

class StellarParticle {
    constructor(canvas, layer) {
        this.canvas = canvas;
        this.layer = layer;
        this.reset();
    }

    reset() {
        this.x = Math.random() * this.canvas.width;
        this.y = Math.random() * this.canvas.height;
        this.size = Math.random() * (this.layer + 1) * 1.2;
        this.vx = (Math.random() - 0.5) * 0.6;
        this.vy = (Math.random() - 0.5) * 0.6;
        this.opacity = Math.random() * 0.4 + 0.1;
    }

    update(mouse) {
        this.x += this.vx;
        this.y += this.vy;

        if (mouse.x !== null) {
            const dx = mouse.x - this.x;
            const dy = mouse.y - this.y;
            const dist = Math.sqrt(dx * dx + dy * dy);
            if (dist < mouse.radius) {
                const force = (mouse.radius - dist) / mouse.radius;
                this.x -= (dx / dist) * force * 1.5;
                this.y -= (dy / dist) * force * 1.5;
            }
        }

        if (this.x < 0 || this.x > this.canvas.width || this.y < 0 || this.y > this.canvas.height) {
            this.reset();
        }
    }

    draw(ctx) {
        ctx.beginPath();
        ctx.fillStyle = `rgba(255, 255, 255, ${this.opacity})`;
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
    }
}

class ScrollObserver {
    constructor() {
        this.options = { threshold: 0.1, rootMargin: '0px 0px -100px 0px' };
        this.init();
    }

    init() {
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('active');
                }
            });
        }, this.options);

        const elements = document.querySelectorAll('.feature-card, .portal-card, .reveal-on-scroll, .subtle-reveal');
        elements.forEach(el => observer.observe(el));
    }
}

// Initialize High-Fidelity Experience
document.addEventListener('DOMContentLoaded', () => {
    // new NeuralSilkEngine('bg-canvas');
    new ScrollObserver();
    
    // Universal Smooth Scrolling
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });
});
