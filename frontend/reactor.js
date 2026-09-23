/**
 * SUVI Holographic Arc Reactor - 60 FPS Canvas Visualizer
 * Simulates an Iron Man JARVIS reactor with reactive sound frequencies
 */

class ArcReactor {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        if (!this.canvas) return;
        this.ctx = this.canvas.getContext('2d');
        
        this.state = 'STANDBY'; // 'STANDBY' | 'LISTENING' | 'PROCESSING' | 'SPEAKING'
        this.rotation = 0;
        this.innerRotation = 0;
        this.pulse = 0;
        this.audioLevel = 0; // 0.0 to 1.0 from Web Audio API
        this.particles = [];
        this.numParticles = 40;

        this.resize();
        window.addEventListener('resize', () => this.resize());
        this.initParticles();
        this.animate();
    }

    resize() {
        const rect = this.canvas.parentElement.getBoundingClientRect();
        const size = Math.min(rect.width, rect.height, 460);
        this.canvas.width = size;
        this.canvas.height = size;
        this.centerX = size / 2;
        this.centerY = size / 2;
        this.radius = size * 0.42;
    }

    initParticles() {
        this.particles = [];
        for (let i = 0; i < this.numParticles; i++) {
            this.particles.push({
                angle: Math.random() * Math.PI * 2,
                distance: Math.random() * (this.radius * 0.8),
                speed: 0.005 + Math.random() * 0.015,
                size: 1 + Math.random() * 2,
                alpha: 0.2 + Math.random() * 0.8
            });
        }
    }

    setState(newState) {
        this.state = newState;
    }

    setAudioLevel(level) {
        // Smooth audio transition
        this.audioLevel = this.audioLevel * 0.7 + level * 0.3;
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        this.render();
    }

    render() {
        const { ctx, canvas, centerX, centerY, radius } = this;
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Dynamic speed based on state
        let rotSpeed = 0.005;
        let innerSpeed = -0.008;
        let glowColor = 'rgba(0, 243, 255, ';
        let coreColor = '#00f3ff';

        if (this.state === 'LISTENING') {
            rotSpeed = 0.015;
            innerSpeed = -0.02;
            glowColor = 'rgba(0, 255, 170, ';
            coreColor = '#00ffaa';
        } else if (this.state === 'PROCESSING') {
            rotSpeed = 0.035;
            innerSpeed = -0.04;
            glowColor = 'rgba(255, 170, 0, ';
            coreColor = '#ffaa00';
        } else if (this.state === 'SPEAKING') {
            rotSpeed = 0.012;
            innerSpeed = -0.015;
            glowColor = 'rgba(0, 150, 255, ';
            coreColor = '#0096ff';
        }

        this.rotation += rotSpeed;
        this.innerRotation += innerSpeed;
        this.pulse += 0.03;

        const pulseScale = 1 + Math.sin(this.pulse) * 0.03 + (this.audioLevel * 0.15);

        // 1. Central Ambient Glow
        const bgGrad = ctx.createRadialGradient(centerX, centerY, 10, centerX, centerY, radius * 1.1);
        bgGrad.addColorStop(0, glowColor + '0.25)');
        bgGrad.addColorStop(0.5, glowColor + '0.06)');
        bgGrad.addColorStop(1, 'transparent');
        ctx.fillStyle = bgGrad;
        ctx.beginPath();
        ctx.arc(centerX, centerY, radius * 1.1, 0, Math.PI * 2);
        ctx.fill();

        // 2. Outer Ring with Ticks
        ctx.save();
        ctx.translate(centerX, centerY);
        ctx.rotate(this.rotation);
        
        ctx.strokeStyle = glowColor + '0.5)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.arc(0, 0, radius, 0, Math.PI * 2);
        ctx.stroke();

        // Ring tick marks
        const ticks = 36;
        for (let i = 0; i < ticks; i++) {
            const angle = (i * Math.PI * 2) / ticks;
            const isMajor = i % 3 === 0;
            const tickLen = isMajor ? 10 : 5;
            const x1 = Math.cos(angle) * (radius - tickLen);
            const y1 = Math.sin(angle) * (radius - tickLen);
            const x2 = Math.cos(angle) * radius;
            const y2 = Math.sin(angle) * radius;

            ctx.strokeStyle = isMajor ? glowColor + '0.9)' : glowColor + '0.3)';
            ctx.lineWidth = isMajor ? 2 : 1;
            ctx.beginPath();
            ctx.moveTo(x1, y1);
            ctx.lineTo(x2, y2);
            ctx.stroke();
        }
        ctx.restore();

        // 3. Middle Segmented Energy Blades
        ctx.save();
        ctx.translate(centerX, centerY);
        ctx.rotate(this.innerRotation);

        const blades = 8;
        const bladeRadius = radius * 0.75 * pulseScale;
        for (let i = 0; i < blades; i++) {
            const startAngle = (i * Math.PI * 2) / blades;
            const endAngle = startAngle + (Math.PI / blades) * 0.7;

            ctx.beginPath();
            ctx.arc(0, 0, bladeRadius, startAngle, endAngle);
            ctx.strokeStyle = glowColor + '0.8)';
            ctx.lineWidth = 3.5;
            ctx.stroke();
        }
        ctx.restore();

        // 4. Energy Particles Orbiting Core
        ctx.save();
        ctx.translate(centerX, centerY);
        this.particles.forEach(p => {
            p.angle += p.speed;
            const px = Math.cos(p.angle) * p.distance;
            const py = Math.sin(p.angle) * p.distance;

            ctx.beginPath();
            ctx.arc(px, py, p.size, 0, Math.PI * 2);
            ctx.fillStyle = glowColor + p.alpha + ')';
            ctx.fill();
        });
        ctx.restore();

        // 5. Sound Frequency Waveform Rings (Audio Reactive)
        if (this.audioLevel > 0.05 || this.state === 'SPEAKING' || this.state === 'LISTENING') {
            ctx.save();
            ctx.translate(centerX, centerY);
            const waveR = radius * 0.5 * (1 + this.audioLevel * 0.35);
            ctx.beginPath();
            ctx.arc(0, 0, waveR, 0, Math.PI * 2);
            ctx.strokeStyle = glowColor + '0.9)';
            ctx.lineWidth = 2 + this.audioLevel * 4;
            ctx.setLineDash([8, 6]);
            ctx.stroke();
            ctx.setLineDash([]);
            ctx.restore();
        }

        // 6. Glowing Inner Reactor Core
        ctx.save();
        ctx.translate(centerX, centerY);

        const coreR = radius * 0.28 * pulseScale;
        const coreGrad = ctx.createRadialGradient(0, 0, 0, 0, 0, coreR);
        coreGrad.addColorStop(0, '#ffffff');
        coreGrad.addColorStop(0.3, coreColor);
        coreGrad.addColorStop(0.8, glowColor + '0.4)');
        coreGrad.addColorStop(1, 'transparent');

        ctx.fillStyle = coreGrad;
        ctx.beginPath();
        ctx.arc(0, 0, coreR, 0, Math.PI * 2);
        ctx.fill();

        // Core Center Triangle / Tech Symbol
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2;
        ctx.beginPath();
        const triR = coreR * 0.45;
        for (let i = 0; i < 3; i++) {
            const angle = (i * Math.PI * 2) / 3 - Math.PI / 2;
            const tx = Math.cos(angle) * triR;
            const ty = Math.sin(angle) * triR;
            if (i === 0) ctx.moveTo(tx, ty);
            else ctx.lineTo(tx, ty);
        }
        ctx.closePath();
        ctx.stroke();

        ctx.restore();
    }
}
