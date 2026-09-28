"""
GLSL Shaders for the PsychoSound Visualizer.
Includes 10 audio-reactive presets:
Presets 1-5: Psychedelic cosmic, liquid, and fractal blooms.
Presets 6-10: Hardcore AIMP / MilkDrop style high-energy strobes, bass cannons,
oscilloscopes, 3D Tron grids, and nuclear plasma reactors.
"""

VERTEX_SHADER = """
#version 330 core
in vec2 in_vert;
out vec2 v_uv;

void main() {
    v_uv = in_vert * 0.5 + 0.5;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
"""

COMMON_GLSL = """
#version 330 core
out vec4 fragColor;
in vec2 v_uv;

uniform vec2  u_resolution;
uniform float u_time;
uniform vec2  u_mouse;
uniform float u_bass;
uniform float u_mid;
uniform float u_high;
uniform float u_vol;
uniform float u_beat;
uniform float u_punch;
uniform float u_strobe;
uniform sampler2D u_spectrum;

#define PI 3.14159265359
#define TWO_PI 6.28318530718

// Cosine based palette generators by Inigo Quilez
vec3 palette( in float t, in vec3 a, in vec3 b, in vec3 c, in vec3 d ) {
    return a + b*cos( 6.28318*(c*t+d) );
}

vec3 rainbowPalette(float t) {
    return palette(t, 
        vec3(0.5, 0.5, 0.5), 
        vec3(0.5, 0.5, 0.5), 
        vec3(1.0, 1.0, 1.0), 
        vec3(0.0, 0.33, 0.67));
}

vec3 cyberPalette(float t) {
    return palette(t, 
        vec3(0.8, 0.5, 0.4), 
        vec3(0.2, 0.4, 0.2), 
        vec3(2.0, 1.0, 1.0), 
        vec3(0.0, 0.25, 0.25));
}

vec3 neonPalette(float t) {
    return palette(t, 
        vec3(0.5, 0.5, 0.5), 
        vec3(0.5, 0.5, 0.5), 
        vec3(1.0, 1.0, 0.5), 
        vec3(0.8, 0.90, 0.30));
}

vec3 firePalette(float t) {
    return palette(t,
        vec3(0.5, 0.5, 0.5),
        vec3(0.5, 0.5, 0.5),
        vec3(2.0, 1.0, 0.0),
        vec3(0.5, 0.20, 0.25));
}

mat2 rotate2D(float angle) {
    float s = sin(angle), c = cos(angle);
    return mat2(c, -s, s, c);
}

float getSpectrum(float x) {
    return texture(u_spectrum, vec2(clamp(x, 0.01, 0.99), 0.5)).r;
}

float getWave(float x) {
    return texture(u_spectrum, vec2(clamp(x, 0.01, 0.99), 0.5)).g;
}

float getPeak(float x) {
    return texture(u_spectrum, vec2(clamp(x, 0.01, 0.99), 0.5)).b;
}

// Applies screen punch bass bounce and mouse parallax
vec2 getCenteredCoord() {
    vec2 p = (gl_FragCoord.xy * 2.0 - u_resolution.xy) / min(u_resolution.x, u_resolution.y);
    p += (u_mouse - 0.5) * 0.3;
    p *= 1.0 - u_punch * 0.22;
    return p;
}

// AIMP Strobe & Inversion flash on hard kicks
vec3 applyAimpStrobe(vec3 col) {
    if (u_strobe > 0.05) {
        col = mix(col, vec3(1.1) - col * 0.4, u_strobe * 0.6);
        col += vec3(1.0, 0.8, 0.9) * (u_strobe * 0.5);
    }
    return col;
}
"""

# Preset 1: Cosmic Kaleidoscope & Fractal Bloom
PRESET_1 = COMMON_GLSL + """
void main() {
    vec2 p = getCenteredCoord();
    vec2 p0 = p;
    
    float segments = 8.0 + floor(u_mid * 4.0);
    float angle = atan(p.y, p.x);
    float r = length(p);
    
    angle = mod(angle, TWO_PI / segments) - (PI / segments);
    p = vec2(cos(angle), sin(angle)) * r;
    
    vec3 finalColor = vec3(0.0);
    float t = u_time * 0.4 + u_bass * 0.2;
    
    for (float i = 0.0; i < 4.0; i += 1.0) {
        p = abs(p) - 0.4 - u_bass * 0.15;
        p *= rotate2D(t * 0.3 + i * 0.5);
        p *= 1.3 + u_beat * 0.05;
        
        float d = length(p) * exp(-length(p0));
        float spec = getSpectrum(i * 0.2 + 0.1);
        vec3 col = rainbowPalette(length(p0) * 0.8 + i * 0.3 + t * 0.5 + spec * 0.5);
        
        d = sin(d * 8.0 + u_time) / 8.0;
        d = abs(d);
        d = pow(0.015 / (d + 0.001), 1.2);
        
        finalColor += col * d * (0.8 + spec * 1.5 + u_high * 0.8);
    }
    
    float core = 0.05 / (length(p0) + 0.02);
    finalColor += vec3(1.0, 0.3, 0.8) * core * (u_bass * 2.2 + u_punch * 3.0);
    finalColor *= 1.0 - smoothstep(1.0, 2.0, length(p0));
    finalColor = applyAimpStrobe(finalColor);
    
    fragColor = vec4(finalColor, 1.0);
}
"""

# Preset 2: Hyper-Dimensional Neon Wormhole / Cyber Tunnel
PRESET_2 = COMMON_GLSL + """
void main() {
    vec2 p = getCenteredCoord();
    float r = length(p);
    float a = atan(p.y, p.x);
    
    float speed = u_time * (1.3 + u_bass * 2.0) + (u_punch * 0.8);
    float z = 1.0 / (r + 0.001) + speed;
    
    a += sin(z * 0.3 + u_time) * (0.4 + u_mid * 0.6);
    
    float sectors = 12.0;
    float rings = abs(sin(z * 4.0));
    float spokes = abs(sin(a * (sectors / 2.0)));
    
    float specIdx = fract(z * 0.1);
    float spec = getSpectrum(specIdx);
    
    float wireframe = pow(rings * spokes, 4.0);
    wireframe = smoothstep(0.1, 0.6, wireframe + spec * 0.5);
    
    vec3 col = cyberPalette(z * 0.05 + u_time * 0.2);
    col += vec3(0.2, 0.8, 1.0) * pow(spec, 1.5) * 2.5;
    col += vec3(1.0, 0.2, 0.5) * u_punch * 2.0;
    
    float fog = smoothstep(0.0, 1.5, r);
    vec3 finalColor = col * wireframe * fog;
    finalColor += vec3(0.4, 0.7, 1.0) * (0.04 / (r + 0.01)) * (0.6 + u_bass * 1.5);
    
    // Chromatic aberration on kicks
    if (u_punch > 0.2) {
        float ca = u_punch * 0.05;
        finalColor.r += getSpectrum(clamp(specIdx + ca, 0.0, 1.0)) * 0.6;
        finalColor.b += getSpectrum(clamp(specIdx - ca, 0.0, 1.0)) * 0.6;
    }
    
    finalColor = applyAimpStrobe(finalColor);
    fragColor = vec4(finalColor, 1.0);
}
"""

# Preset 3: Psychedelic Acid Liquid / Domain Warping Plasma
PRESET_3 = COMMON_GLSL + """
float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    return mix(
        mix(hash(i), hash(i + vec2(1.0, 0.0)), f.x),
        mix(hash(i + vec2(0.0, 1.0)), hash(i + vec2(1.0, 1.0)), f.x),
        f.y
    );
}

float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    mat2 rot = rotate2D(0.5);
    for (int i = 0; i < 5; i++) {
        v += a * noise(p);
        p = rot * p * 2.0;
        a *= 0.5;
    }
    return v;
}

void main() {
    vec2 p = getCenteredCoord();
    float t = u_time * 0.35;
    
    vec2 q = vec2(
        fbm(p + vec2(0.0, 0.0) + t * 0.4 + u_bass * 0.4),
        fbm(p + vec2(5.2, 1.3) + t * 0.3 - u_mid * 0.3)
    );
    
    vec2 r = vec2(
        fbm(p + 4.0 * q + vec2(1.7, 9.2) + t * 0.2 + u_punch * 0.4),
        fbm(p + 4.0 * q + vec2(8.3, 2.8) + t * 0.25)
    );
    
    float f = fbm(p + 4.0 * r);
    float spec = getSpectrum(f);
    
    vec3 col = mix(vec3(0.1, 0.05, 0.2), vec3(0.9, 0.2, 0.6), clamp((f * f) * 4.0, 0.0, 1.0));
    col = mix(col, vec3(0.0, 0.9, 0.8), clamp(length(q), 0.0, 1.0));
    col = mix(col, vec3(1.0, 0.8, 0.2), clamp(length(r.x), 0.0, 1.0));
    
    col += vec3(0.3, 0.9, 1.0) * pow(spec, 2.0) * 2.2;
    col += vec3(1.0, 0.4, 0.8) * u_high * pow(f, 3.0) * 2.5;
    
    float contours = sin(f * 20.0 + u_time * 2.0 + u_bass * 5.0);
    contours = smoothstep(0.8, 0.98, 1.0 - abs(contours));
    col += neonPalette(f + u_time * 0.1) * contours * 0.9;
    
    col = applyAimpStrobe(col);
    fragColor = vec4(col, 1.0);
}
"""

# Preset 4: Electric Audio Nebula & Sacred Geometry Core
PRESET_4 = COMMON_GLSL + """
void main() {
    vec2 p = getCenteredCoord();
    p *= rotate2D(u_time * 0.12 + u_bass * 0.15);
    
    float dist = length(p);
    float angle = atan(p.y, p.x);
    float normAngle = (angle + PI) / TWO_PI;
    if (normAngle > 0.5) normAngle = 1.0 - normAngle;
    normAngle *= 2.0;
    
    float spec = getSpectrum(normAngle);
    vec3 col = vec3(0.0);
    
    float targetR = 0.45 + spec * 0.4 + u_bass * 0.15;
    float ring = smoothstep(0.02 + u_high * 0.03, 0.0, abs(dist - targetR));
    col += neonPalette(normAngle + u_time * 0.2) * ring * 3.5;
    
    float innerR = 0.25 + getSpectrum(1.0 - normAngle) * 0.25;
    float innerRing = smoothstep(0.012, 0.0, abs(dist - innerR));
    col += vec3(0.2, 0.8, 1.0) * innerRing * 3.0;
    
    float symmetry = 8.0;
    float starA = mod(angle + u_time * 0.2, TWO_PI / symmetry) - (PI / symmetry);
    vec2 starP = vec2(cos(starA), sin(starA)) * dist;
    float ray = 0.006 / (abs(starP.y) + 0.001);
    col += cyberPalette(dist * 2.0 - u_time * 0.5) * ray * (0.3 + u_mid * 0.8) * smoothstep(0.9, 0.1, dist);
    
    float core = 0.045 / (dist + 0.01);
    col += vec3(1.0, 0.5, 0.2) * core * (u_bass * 3.0 + u_punch * 3.5);
    
    float dust = sin(p.x * 25.0 + u_time) * cos(p.y * 25.0 - u_time);
    dust = smoothstep(0.9, 1.0, dust);
    col += vec3(1.0, 0.8, 1.0) * dust * u_high * 2.0;
    
    col = applyAimpStrobe(col);
    fragColor = vec4(col, 1.0);
}
"""

# Preset 5: Cyberpunk Mandelbulb / Fractal Matrix
PRESET_5 = COMMON_GLSL + """
void main() {
    vec2 p = getCenteredCoord();
    p *= rotate2D(u_time * 0.15 + (u_mouse.x - 0.5));
    
    vec2 z = p;
    vec2 c = vec2(-0.7 + sin(u_time * 0.2) * 0.1 + u_bass * 0.08,
                  0.27015 + cos(u_time * 0.3) * 0.1 + u_mid * 0.08);
    
    float trap1 = 1e10;
    float trap2 = 1e10;
    float n = 0.0;
    
    for (int i = 0; i < 40; i++) {
        z = vec2(z.x * z.x - z.y * z.y, 2.0 * z.x * z.y) + c;
        trap1 = min(trap1, length(z - vec2(sin(u_time), cos(u_time)) * 0.5));
        trap2 = min(trap2, abs(z.x * z.y));
        if (dot(z, z) > 4.0) {
            n = float(i);
            break;
        }
    }
    
    float spec = getSpectrum(clamp(n / 40.0, 0.0, 1.0));
    vec3 col = vec3(0.0);
    col += vec3(0.9, 0.1, 0.5) * (0.08 / (trap1 + 0.05)) * (0.8 + u_bass * 1.5);
    col += vec3(0.1, 0.8, 1.0) * (0.04 / (trap2 + 0.02)) * (0.8 + u_high * 2.5);
    
    if (n > 0.0) {
        float f = n / 40.0;
        col += rainbowPalette(f + u_time * 0.1 + spec * 0.5) * 0.7;
    }
    
    col += vec3(0.3, 0.1, 0.3) * u_punch * 1.5;
    col = applyAimpStrobe(col);
    fragColor = vec4(col, 1.0);
}
"""

# =========================================================================
# HARDCORE AIMP / MILKDROP STYLE PRESETS (6 - 10)
# =========================================================================

# Preset 6: AIMP Bass Cannon & Neon Strobe
PRESET_6 = COMMON_GLSL + """
void main() {
    vec2 p = getCenteredCoord();
    
    // Intense camera shake on heavy kick
    if (u_punch > 0.3) {
        p += vec2(sin(u_time * 80.0), cos(u_time * 80.0)) * u_punch * 0.025;
    }
    
    float dist = length(p);
    float angle = atan(p.y, p.x);
    
    // Multi-spoke radial spectrum cannon
    float numSpikes = 64.0;
    float normAngle = abs(fract(angle / TWO_PI * (numSpikes / 2.0)) - 0.5) * 2.0;
    float specCoord = abs(angle) / PI;
    float spec = getSpectrum(specCoord);
    float peak = getPeak(specCoord);
    
    vec3 col = vec3(0.0);
    
    // Pulsing bass cannon rings
    for (float i = 1.0; i <= 5.0; i += 1.0) {
        float ringRad = i * 0.18 + u_bass * 0.08;
        // Shockwave ripples
        ringRad += fract(u_time * 1.5 - i * 0.2) * (u_punch * 0.4);
        float ringThick = 0.008 + (u_punch * 0.015);
        float ring = smoothstep(ringThick, 0.0, abs(dist - ringRad));
        
        vec3 rCol = (i == 1.0) ? vec3(1.0, 0.1, 0.3) : cyberPalette(i * 0.2 + u_time);
        col += rCol * ring * (2.5 + u_bass * 2.0);
    }
    
    // Aggressive laser spikes piercing outward from the center
    float spikeLength = 0.25 + spec * 0.7 + peak * 0.5;
    float spikeGlow = smoothstep(0.03, 0.0, abs(dist - spikeLength) * normAngle * 2.0);
    col += vec3(0.0, 0.9, 1.0) * spikeGlow * (2.0 + peak * 3.0);
    
    // Central Nuclear Bass Core
    float core = 0.06 / (dist + 0.015);
    col += vec3(1.0, 0.05, 0.2) * core * (u_bass * 3.5 + u_punch * 5.0);
    
    // Strobe RGB split glitch on bass drops
    if (u_strobe > 0.1) {
        float rOff = getSpectrum(clamp(specCoord + 0.05, 0.0, 1.0));
        float bOff = getSpectrum(clamp(specCoord - 0.05, 0.0, 1.0));
        col.r += rOff * u_strobe * 1.5;
        col.b += bOff * u_strobe * 1.5;
        col = mix(col, vec3(1.0) - col, u_strobe * 0.7);
    }
    
    fragColor = vec4(col, 1.0);
}
"""

# Preset 7: Cyber Oscilloscope & Tesla Lightning Ribbon
PRESET_7 = COMMON_GLSL + """
void main() {
    vec2 p = getCenteredCoord();
    vec2 uv = gl_FragCoord.xy / u_resolution.xy;
    
    vec3 col = vec3(0.0);
    
    // 3D Perspective Grid at the bottom
    if (p.y < -0.15) {
        float depth = 1.0 / (abs(p.y + 0.15) + 0.05);
        float gridX = abs(sin((p.x * depth + (u_mouse.x - 0.5) * 2.0) * 10.0));
        float gridZ = abs(sin((depth - u_time * (4.0 + u_bass * 3.0)) * 6.0));
        float grid = smoothstep(0.85, 0.98, max(gridX, gridZ));
        
        float specAtDepth = getSpectrum(fract(depth * 0.1));
        col += vec3(0.1, 0.5, 1.0) * grid * (0.8 + specAtDepth * 2.0) * exp(-abs(p.y) * 2.0);
    }
    
    // Real-time time-domain laser oscilloscope waveform
    float waveX = uv.x;
    float waveY = getWave(waveX) * (0.45 + u_bass * 0.35);
    
    // Electric Tesla arc noise modulation
    float spark = sin(waveX * 80.0 + u_time * 30.0) * (u_high * 0.06);
    float totalWaveY = waveY + spark;
    
    float distToWave = abs(p.y - totalWaveY);
    
    // Laser beam core & bloom
    float laserBeam = 0.004 / (distToWave + 0.001);
    float laserBloom = exp(-distToWave * 30.0) * 1.8;
    
    vec3 laserColor = mix(vec3(0.0, 1.0, 0.8), vec3(1.0, 0.1, 0.6), abs(p.x));
    col += laserColor * laserBeam * (1.2 + u_bass * 1.5);
    col += vec3(0.2, 0.6, 1.0) * laserBloom * (1.0 + u_punch * 3.0);
    
    // Secondary harmonic wave
    float wave2Y = -getWave(1.0 - waveX) * (0.25 + u_mid * 0.25);
    float d2 = abs(p.y - wave2Y);
    col += vec3(1.0, 0.8, 0.1) * (0.003 / (d2 + 0.002)) * (1.0 + u_high * 2.0);
    
    // High-voltage lightning discharge bolts on beat punch
    if (u_punch > 0.25) {
        float boltX = sin(p.y * 30.0 + u_time * 50.0) * (u_punch * 0.15);
        float boltDist = abs(p.x - boltX);
        col += vec3(1.0, 1.0, 1.0) * (0.003 / (boltDist + 0.001)) * (u_punch * 2.0);
    }
    
    col = applyAimpStrobe(col);
    fragColor = vec4(col, 1.0);
}
"""

# Preset 8: Tron 3D Cyber Grid & Neon Peak Equalizer
PRESET_8 = COMMON_GLSL + """
void main() {
    vec2 p = getCenteredCoord();
    vec3 col = vec3(0.01, 0.0, 0.04);
    
    // Giant Retro Neon Synthwave Sun
    vec2 sunPos = p - vec2(0.0, 0.15);
    float sunDist = length(sunPos);
    if (sunDist < 0.35 + u_bass * 0.08) {
        float sunY = sunPos.y / 0.35;
        // Sun horizontal laser slices
        float slice = abs(sin((sunY + 1.0) * 18.0));
        float sliceMask = smoothstep(0.2, 0.7, slice + (1.0 - sunY) * 0.4);
        
        vec3 sunGrad = mix(vec3(1.0, 0.1, 0.5), vec3(1.0, 0.9, 0.2), clamp(sunY * 0.5 + 0.5, 0.0, 1.0));
        col += sunGrad * sliceMask * (1.5 + u_punch * 1.5);
    }
    
    // 3D Tron Equalizer Grid (Lower Half)
    if (p.y < 0.0) {
        float horizonDist = -p.y;
        float z = 1.0 / (horizonDist + 0.01);
        float x = p.x * z;
        
        // Equalizer column bars in 3D
        float colWidth = 0.5;
        float colIdx = floor((x + 10.0) / colWidth);
        float normBand = clamp(fract(colIdx * 0.08), 0.02, 0.98);
        
        float specHeight = getSpectrum(normBand) * 1.8 + getPeak(normBand) * 1.0;
        float barX = mod(x + 10.0, colWidth) - colWidth * 0.5;
        
        // Peak equalizer bar rendering
        if (abs(barX) < 0.18 && z > 2.0 && z < 45.0) {
            float barTop = specHeight * (z * 0.035);
            if (p.y > -barTop && p.y <= 0.0) {
                float intensity = (p.y / -barTop);
                vec3 barCol = mix(vec3(0.0, 1.0, 0.7), vec3(1.0, 0.0, 0.5), intensity);
                col += barCol * (1.5 + u_bass);
            }
        }
        
        // Perspective Grid lines
        float lineX = abs(sin(x * 3.0));
        float lineZ = abs(sin(z * 0.5 - u_time * (5.0 + u_bass * 4.0)));
        float grid = smoothstep(0.88, 0.98, max(lineX, lineZ));
        col += vec3(0.0, 0.8, 1.0) * grid * (0.6 + u_bass * 0.8) * exp(-horizonDist * 2.0);
    }
    
    // Floating star particles on high frequencies
    float stars = sin(p.x * 60.0 + u_time) * cos(p.y * 60.0);
    stars = smoothstep(0.97, 1.0, stars);
    col += vec3(1.0, 0.9, 1.0) * stars * (u_high * 3.0 + u_punch * 2.0);
    
    col = applyAimpStrobe(col);
    fragColor = vec4(col, 1.0);
}
"""

# Preset 9: Acid Hyperspace Vortex (MilkDrop Trip)
PRESET_9 = COMMON_GLSL + """
void main() {
    vec2 p = getCenteredCoord();
    
    // Milkdrop-style infinite rotational feedback warp
    float r = length(p);
    float a = atan(p.y, p.x);
    
    // Hyper-vortex rotation
    float spinSpeed = u_time * (1.2 + u_bass * 1.8) + (u_punch * 0.8);
    a += 2.5 * log(r + 0.001) + spinSpeed;
    
    // Symmetry fold
    float kFold = 6.0 + floor(u_mid * 3.0);
    a = abs(mod(a, TWO_PI / kFold) - (PI / kFold));
    
    vec2 uvWarp = vec2(cos(a), sin(a)) * pow(r, 0.6 + u_punch * 0.2);
    
    // Spectrum lookup based on spiral coords
    float specUv = fract(length(uvWarp) * 1.2 - u_time * 0.4);
    float spec = getSpectrum(specUv);
    
    vec3 col = vec3(0.0);
    
    // Psychedelic spiraling neon ribbons
    for (float i = 1.0; i <= 4.0; i += 1.0) {
        float spiral = sin(uvWarp.x * (8.0 * i) + u_time * 3.0 + u_bass * 4.0) *
                       cos(uvWarp.y * (8.0 * i) - u_time * 2.0);
        spiral = smoothstep(0.4, 0.95, abs(spiral));
        
        vec3 ribbonCol = rainbowPalette(i * 0.25 + u_time * 0.3 + spec * 0.6);
        col += ribbonCol * spiral * (1.2 + spec * 2.0);
    }
    
    // Pulsing central black hole / singularity
    float coreHole = smoothstep(0.08, 0.02, r);
    col *= (1.0 - coreHole * 0.8);
    
    // Corona around singularity
    float corona = 0.02 / (abs(r - (0.1 + u_bass * 0.08)) + 0.005);
    col += vec3(1.0, 0.2, 0.8) * corona * (1.5 + u_punch * 3.0);
    
    // Negative-color strobe pulses on bass hits
    if (u_strobe > 0.1) {
        col = mix(col, vec3(1.2) - col, u_strobe * 0.85);
    }
    
    fragColor = vec4(col, 1.0);
}
"""

# Preset 10: Nuclear Core Meltdown (Plasma Shockwave)
PRESET_10 = COMMON_GLSL + """
void main() {
    vec2 p = getCenteredCoord();
    
    float dist = length(p);
    float angle = atan(p.y, p.x);
    
    // Explosive shockwave distortion ring expanding from center
    float shockPhase = fract(u_time * 1.8);
    float shockDist = shockPhase * 1.3;
    float inShock = smoothstep(0.12, 0.0, abs(dist - shockDist));
    
    // Shockwave bends space
    p += normalize(p) * inShock * (u_punch * 0.12);
    dist = length(p);
    
    // Rotating magnetic containment field rings
    vec3 col = vec3(0.0);
    
    for (float i = 1.0; i <= 3.0; i += 1.0) {
        vec2 rp = p * rotate2D(u_time * (i * 0.6) + u_bass * 0.4);
        float ringA = abs(sin(atan(rp.y, rp.x) * (4.0 * i)));
        float rR = 0.35 * i + u_bass * 0.05;
        float ringVal = smoothstep(0.015 + u_punch * 0.01, 0.0, abs(length(rp) - rR));
        col += firePalette(i * 0.3 + u_time * 0.5) * ringVal * (2.0 + ringA * 2.5);
    }
    
    // Solar plasma tendrils / arc discharges
    float specNorm = fract((angle + PI) / TWO_PI);
    float spec = getSpectrum(specNorm);
    float arcLen = 0.2 + spec * 0.6 + u_bass * 0.3;
    float arc = smoothstep(0.02, 0.0, abs(dist - arcLen));
    col += vec3(1.0, 0.9, 0.2) * arc * (2.0 + u_high * 3.0);
    
    // Hyper-intense Reactor Core
    float coreGlow = 0.08 / (dist + 0.01);
    col += vec3(1.0, 0.3, 0.05) * coreGlow * (2.5 + u_bass * 3.0);
    col += vec3(1.0, 1.0, 0.9) * pow(coreGlow * 0.2, 2.0) * (2.0 + u_punch * 5.0);
    
    // Shockwave flash
    col += vec3(1.0, 0.5, 0.2) * inShock * (u_punch * 2.5);
    
    col = applyAimpStrobe(col);
    fragColor = vec4(col, 1.0);
}
"""

# Preset 11: Club Laser Rave Arena
PRESET_11 = COMMON_GLSL + """
void main() {
    vec2 p = getCenteredCoord();
    vec3 col = vec3(0.01, 0.01, 0.03);
    
    // Laser projector base at the bottom
    vec2 origin = vec2(0.0, -0.9);
    vec2 d = p - origin;
    float dist = length(d);
    float angle = atan(d.x, d.y); // angle from vertical
    
    // 16 Laser Beams fanning out across the arena
    float numLasers = 16.0;
    for (float i = 0.0; i < 16.0; i += 1.0) {
        float normIdx = i / numLasers;
        float spec = getSpectrum(normIdx);
        
        // Dynamic laser sweep
        float targetAngle = (normIdx - 0.5) * 2.2 + sin(u_time * 1.5 + i * 0.4) * (0.3 + u_mid * 0.3);
        float beamDist = abs(angle - targetAngle) * dist;
        
        // Laser core & volumetric bloom
        float beamCore = 0.002 / (beamDist + 0.0008);
        float beamBloom = exp(-beamDist * 40.0) * (0.8 + spec * 2.5);
        
        vec3 laserCol = neonPalette(normIdx + u_time * 0.1);
        col += laserCol * (beamCore + beamBloom) * (1.0 + u_bass * 1.5);
    }
    
    // Smokey club volumetric fog
    float smoke = sin(p.x * 4.0 + u_time * 0.8) * cos(p.y * 4.0 - u_time * 0.6);
    smoke += sin(p.x * 8.0 - u_time) * cos(p.y * 8.0 + u_time);
    col += vec3(0.05, 0.1, 0.2) * (smoke * 0.5 + 0.5) * smoothstep(-0.8, 0.5, p.y);
    
    // Ceiling strobe blinds flashing on kicks
    if (p.y > 0.5) {
        float strobePanel = abs(sin(p.x * 20.0));
        strobePanel = smoothstep(0.4, 0.95, strobePanel);
        col += vec3(1.0, 0.95, 1.0) * strobePanel * (u_strobe * 2.5 + u_punch * 1.5);
    }
    
    col = applyAimpStrobe(col);
    fragColor = vec4(col, 1.0);
}
"""

# Preset 12: Cyber Bio-Hazard Skull
PRESET_12 = COMMON_GLSL + """
void main() {
    vec2 p = getCenteredCoord();
    vec2 p_orig = p;
    
    // Symmetry fold
    p.x = abs(p.x);
    
    vec3 col = vec3(0.01, 0.0, 0.02);
    
    // Rotating biohazard gear behind
    float bgDist = length(p_orig);
    float bgAngle = atan(p_orig.y, p_orig.x) + u_time * 0.5;
    float gear = abs(sin(bgAngle * 6.0));
    float gearRing = smoothstep(0.02, 0.0, abs(bgDist - (0.55 + u_bass * 0.1)));
    col += vec3(0.0, 0.8, 0.5) * gearRing * (1.0 + gear * 2.0) * (0.8 + u_bass);
    
    // Cranium
    vec2 headP = p - vec2(0.0, 0.12);
    float cranium = length(headP * vec2(1.0, 1.15)) - 0.28;
    
    // Jaw moving on bass drops
    vec2 jawP = p - vec2(0.0, -0.22 - u_punch * 0.08 - u_bass * 0.05);
    float jaw = length(max(abs(jawP) - vec2(0.12, 0.08), 0.0)) - 0.02;
    
    // Eye Sockets
    vec2 eyeP = p - vec2(0.12, 0.10);
    float eye = length(eyeP * vec2(1.2, 0.9)) - 0.065;
    
    // Nose Cavity
    vec2 noseP = p - vec2(0.0, -0.05);
    float nose = length(noseP * vec2(1.5, 1.0)) - 0.035;
    
    // Combine skull silhouette
    float skull = min(cranium, jaw);
    skull = max(skull, -eye);
    skull = max(skull, -nose);
    
    // Holographic neon outline & cyber mesh
    float skullOutline = smoothstep(0.015 + u_punch * 0.01, 0.0, abs(skull));
    float mesh = abs(sin(p.y * 50.0 + u_time * 3.0)) * abs(sin(p.x * 50.0));
    mesh = smoothstep(0.7, 0.98, mesh);
    
    vec3 skullCol = mix(vec3(0.0, 1.0, 0.8), vec3(1.0, 0.0, 0.4), u_punch);
    col += skullCol * skullOutline * 3.0;
    if (skull < 0.0) {
        col += vec3(0.0, 0.3, 0.4) * mesh * (1.0 + u_bass * 2.0);
    }
    
    // Laser beams shooting out from eye sockets on high frequencies
    if (p_orig.y > 0.05 && p_orig.y < 0.15) {
        float laserY = abs(p_orig.y - 0.10);
        float eyeBeam = 0.003 / (laserY + 0.001);
        col += vec3(1.0, 0.1, 0.1) * eyeBeam * (u_high * 2.5 + u_punch * 2.0);
    }
    
    // Teeth grid in jaw
    if (abs(jawP.y) < 0.04 && jawP.x < 0.12) {
        float teeth = abs(sin(jawP.x * 40.0));
        col += vec3(0.0, 1.0, 0.8) * smoothstep(0.6, 0.95, teeth) * 2.0;
    }
    
    col = applyAimpStrobe(col);
    fragColor = vec4(col, 1.0);
}
"""

# Preset 13: Gargantua Black Hole Flare
PRESET_13 = COMMON_GLSL + """
void main() {
    vec2 p = getCenteredCoord();
    
    float dist = length(p);
    float angle = atan(p.y, p.x);
    
    // Relativistic gravitational lensing (light bending around event horizon)
    float rs = 0.22; // Schwarzschild radius
    float lensFactor = rs / (dist + 0.0001);
    vec2 bentP = p * (1.0 + lensFactor * 0.4);
    float bentDist = length(bentP);
    
    vec3 col = vec3(0.0);
    
    // Swirling Accretion Disk (elliptic projection)
    vec2 diskP = vec2(bentP.x, bentP.y * 2.8 + bentP.x * 0.4);
    float diskR = length(diskP);
    
    if (diskR > rs * 1.1 && diskR < 0.85 + u_bass * 0.15) {
        float diskAngle = atan(diskP.y, diskP.x) - u_time * (2.5 + u_bass * 2.0);
        float spiral = sin(diskAngle * 4.0 + log(diskR) * 10.0);
        float spec = getSpectrum(fract(diskR * 1.2));
        
        // Doppler blue-shift on approaching side (left side is brighter & bluer)
        float doppler = smoothstep(-0.5, 0.5, -diskP.x / diskR);
        vec3 diskCol = mix(vec3(1.0, 0.3, 0.05), vec3(0.3, 0.8, 1.0), doppler);
        
        float diskIntensity = smoothstep(0.85, rs * 1.2, diskR) * (0.8 + spiral * 0.4 + spec * 2.0);
        col += diskCol * diskIntensity * (2.0 + u_punch * 3.0);
    }
    
    // Relativistic Polar Plasma Jets shooting outward
    float jetDist = abs(bentP.x) + abs(bentP.y) * 0.15;
    if (abs(bentP.y) > rs) {
        float jet = 0.006 / (jetDist + 0.003);
        col += vec3(0.4, 0.8, 1.0) * jet * (u_bass * 2.0 + u_punch * 3.5);
    }
    
    // Event Horizon (Absolute Pitch Black Core)
    if (dist < rs) {
        col = vec3(0.0);
    }
    
    // Blazing Photon Sphere Ring
    float photonRing = smoothstep(0.012, 0.0, abs(dist - rs));
    col += vec3(1.0, 0.9, 0.8) * photonRing * (4.0 + u_punch * 5.0);
    
    // Gravitational shockwave ripples on beat
    float ripple = abs(sin(dist * 25.0 - u_time * 6.0));
    col += vec3(0.1, 0.4, 0.8) * smoothstep(0.9, 0.98, ripple) * u_punch * 2.0;
    
    col = applyAimpStrobe(col);
    fragColor = vec4(col, 1.0);
}
"""

# Preset 14: Hyperspace Starfield Warp
PRESET_14 = COMMON_GLSL + """
void main() {
    vec2 p = getCenteredCoord();
    
    float dist = length(p);
    float angle = atan(p.y, p.x);
    
    // Hyperspeed acceleration on kicks
    float warpSpeed = u_time * (2.0 + u_bass * 3.0) + (u_punch * 1.5);
    float streakLen = 0.15 + u_punch * 0.6 + u_bass * 0.3;
    
    vec3 col = vec3(0.005, 0.0, 0.015);
    
    // 3 Layers of 3D Warp Stars
    for (float layer = 1.0; layer <= 3.0; layer += 1.0) {
        float numRays = 40.0 * layer;
        float rayAngle = mod(angle, TWO_PI / numRays) - (PI / numRays);
        float rayIdx = floor(angle / (TWO_PI / numRays));
        
        // Star radial streak
        float starZ = fract(dist * (1.5 * layer) - warpSpeed * (0.3 * layer));
        float starStreak = smoothstep(streakLen, 0.0, abs(dist - starZ));
        float starSpoke = smoothstep(0.008 * dist, 0.0, abs(rayAngle) * dist);
        
        float spec = getSpectrum(fract(rayIdx * 0.05));
        vec3 starCol = rainbowPalette(rayIdx * 0.1 + u_time * 0.2 + spec * 0.5);
        
        col += starCol * (starStreak * starSpoke) * (2.5 + spec * 3.0);
    }
    
    // Supersonic Mach Shock Cones on kicks
    if (u_punch > 0.15) {
        for (float j = 1.0; j <= 3.0; j += 1.0) {
            float coneR = fract(u_time * 2.0 - j * 0.3) * 1.4;
            float cone = smoothstep(0.02, 0.0, abs(dist - coneR));
            col += vec3(0.0, 0.9, 1.0) * cone * (u_punch * 2.5);
        }
    }
    
    // Center hyperspace jump core
    float core = 0.035 / (dist + 0.01);
    col += vec3(0.8, 0.9, 1.0) * core * (1.5 + u_punch * 4.0);
    
    col = applyAimpStrobe(col);
    fragColor = vec4(col, 1.0);
}
"""

# Preset 15: 🔥 ВООБЩЕ ЖЕСТЬ: ACID GLITCH CARNAGE 🔥 (ULTIMATE INSANITY)
PRESET_15 = COMMON_GLSL + """
float glitchNoise(vec2 p) {
    return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453);
}

void main() {
    vec2 uv = gl_FragCoord.xy / u_resolution.xy;
    vec2 p = getCenteredCoord();
    
    // HARDCORE CAMERA SHAKE & EARTHQUAKE ON BASS
    if (u_punch > 0.2) {
        vec2 shake = vec2(
            sin(u_time * 95.0 + p.y * 20.0),
            cos(u_time * 85.0 + p.x * 20.0)
        ) * (u_punch * 0.04);
        p += shake;
    }
    
    // HORIZONTAL SCANLINE TEARING & GLITCH CHUNKS
    float sliceY = floor(uv.y * 35.0);
    float sliceNoise = glitchNoise(vec2(sliceY, floor(u_time * 24.0)));
    if (sliceNoise > 0.65 || u_punch > 0.4) {
        float tearOffset = (sliceNoise - 0.5) * (0.12 + u_punch * 0.25);
        p.x += tearOffset;
        uv.x += tearOffset * 0.5;
    }
    
    // 3-WAY CHROMATIC SEPARATION ON STEREO TRANSIENTS
    float ca = 0.03 + u_punch * 0.08 + u_bass * 0.04;
    
    // HYPER-FRACTAL CARNAGE FOLDING
    vec3 col = vec3(0.0);
    
    for (int ch = 0; ch < 3; ch++) {
        vec2 cp = p;
        if (ch == 0) cp.x += ca; // Red channel displaced
        if (ch == 2) cp.x -= ca; // Blue channel displaced
        
        float t = u_time * (1.8 + u_bass * 2.5) + float(ch) * 0.2;
        mat2 rot = rotate2D(t * 0.5 + u_mid);
        
        float acc = 0.0;
        for (float i = 0.0; i < 5.0; i += 1.0) {
            cp = abs(cp * rot) - vec2(0.35 + u_punch * 0.3, 0.25 + u_bass * 0.2);
            float d = length(cp);
            float spec = getSpectrum(i * 0.2 + float(ch) * 0.1);
            acc += (0.015 / (d + 0.005)) * (1.0 + spec * 2.5 + u_high * 2.0);
        }
        
        if (ch == 0) col.r = acc * 1.4;
        if (ch == 1) col.g = acc * 0.9;
        if (ch == 2) col.b = acc * 1.8;
    }
    
    // DIGITAL NOISE & CORRUPT MATRIX LINES
    float dNoise = glitchNoise(p * 50.0 + fract(u_time * 30.0));
    col += vec3(dNoise * 0.2) * (1.0 + u_high * 2.0);
    
    // CYBERNETIC EXPLOSIVE SHOCKWAVE FROM CENTER
    float r = length(p);
    float boom = fract(u_time * 3.0);
    float boomRing = smoothstep(0.08, 0.0, abs(r - boom * 1.2));
    col += vec3(1.0, 0.2, 0.6) * boomRing * (u_punch * 4.0);
    
    // HYPER-STROBE & EPILEPTIC REALITY INVERSION
    if (u_strobe > 0.1 || u_punch > 0.6) {
        float strobePow = max(u_strobe, u_punch);
        // Violent negative color inversion
        col = mix(col, vec3(1.4) - col * 0.3, strobePow * 0.9);
        col += vec3(1.0, 0.2, 0.5) * (strobePow * 0.6);
    }
    
    // Hard contrast limiter & saturation burn
    col = pow(col, vec3(1.2));
    col = clamp(col, 0.0, 2.5);
    
    fragColor = vec4(col, 1.0);
}
"""

PRESETS = [
    # Classic Psychedelic (1-5)
    ("Cosmic Kaleidoscope", PRESET_1),
    ("Neon Cyber Wormhole", PRESET_2),
    ("Liquid Acid Plasma", PRESET_3),
    ("Sacred Audio Core", PRESET_4),
    ("Fractal Cyber Matrix", PRESET_5),
    # Hardcore AIMP / MilkDrop (6-10)
    ("AIMP Bass Cannon & Strobe", PRESET_6),
    ("Cyber Oscilloscope Tesla", PRESET_7),
    ("Tron 3D Grid & Equalizer", PRESET_8),
    ("Acid Hyperspace Vortex", PRESET_9),
    ("Nuclear Core Meltdown", PRESET_10),
    # Mega Hardcore & Space (11-14)
    ("Club Laser Rave Arena", PRESET_11),
    ("Cyber Bio-Hazard Skull", PRESET_12),
    ("Gargantua Black Hole Flare", PRESET_13),
    ("Hyperspace Starfield Warp", PRESET_14),
    # Ultimate Carnage (15)
    ("TOTAL CARNAGE: Acid Glitch Apocalypse", PRESET_15),
]

