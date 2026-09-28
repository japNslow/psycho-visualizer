"""
PsychoSound Visualizer
Real-time audio visualizer with psychedelic & Hardcore AIMP/MilkDrop GPU shaders.
Captures system audio loopback (browser, YouTube, Spotify, games) via WASAPI.
"""

import sys
import time
import math
import numpy as np
import pygame
import moderngl

from audio_engine import AudioAnalyzer
from shaders import VERTEX_SHADER, PRESETS

HUD_VS = """
#version 330 core
in vec2 in_vert;
out vec2 v_uv;
void main() {
    v_uv = in_vert * 0.5 + 0.5;
    v_uv.y = 1.0 - v_uv.y;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
"""

HUD_FS = """
#version 330 core
in vec2 v_uv;
out vec4 fragColor;
uniform sampler2D u_hud_tex;
void main() {
    fragColor = texture(u_hud_tex, v_uv);
}
"""

def safe_set_uniform(prog, name, value):
    """Sets uniform if it exists and wasn't optimized out by the GLSL compiler."""
    if name in prog:
        prog[name].value = value

class PsychoVisualizerApp:
    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height
        self.fullscreen = False
        
        # Initialize Pygame and ModernGL
        pygame.init()
        pygame.font.init()
        pygame.display.set_caption("PsychoSound Visualizer | Audio Reactive Shaders")
        
        self.screen = pygame.display.set_mode(
            (self.width, self.height),
            pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
        )
        
        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        
        # Audio analyzer
        self.audio = AudioAnalyzer(sample_rate=44100, buffer_size=2048, num_bands=64)
        
        # Fullscreen quad geometry
        quad_vertices = np.array([
            -1.0, -1.0,
             1.0, -1.0,
            -1.0,  1.0,
            -1.0,  1.0,
             1.0, -1.0,
             1.0,  1.0,
        ], dtype='f4')
        
        self.vbo = self.ctx.buffer(quad_vertices.tobytes())
        
        # Compile all preset shaders
        self.programs = []
        self.preset_names = []
        for name, fs_source in PRESETS:
            try:
                prog = self.ctx.program(vertex_shader=VERTEX_SHADER, fragment_shader=fs_source)
                self.programs.append(prog)
                self.preset_names.append(name)
            except Exception as e:
                print(f"[ERROR] Failed to compile shader '{name}': {e}")
                
        if not self.programs:
            raise RuntimeError("No shaders could be compiled!")
            
        # Default to Preset 6 (AIMP Bass Cannon) to immediately show the new hardcore effect!
        self.current_preset = 5 if len(self.programs) >= 6 else 0
        self.current_program = self.programs[self.current_preset]
        self.vao = self.ctx.simple_vertex_array(self.current_program, self.vbo, 'in_vert')
        
        # HUD program and texture
        self.hud_prog = self.ctx.program(vertex_shader=HUD_VS, fragment_shader=HUD_FS)
        self.hud_vao = self.ctx.simple_vertex_array(self.hud_prog, self.vbo, 'in_vert')
        self.hud_tex = self.ctx.texture((self.width, self.height), 4)
        self.hud_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        self.hud_font_large = pygame.font.SysFont('consolas', 24, bold=True)
        self.hud_font_small = pygame.font.SysFont('consolas', 16)
        self.show_hud = True
        self.hud_timeout = 8.0
        self.last_interaction_time = time.time()
        
        # 4-Channel Texture (64x1, RGBA float32): R=Spectrum, G=Waveform, B=RawPeak, A=Punch
        self.spectrum_tex = self.ctx.texture((64, 1), 4, dtype='f4')
        self.spectrum_tex.filter = (moderngl.LINEAR, moderngl.LINEAR)
        self.spectrum_tex.repeat_x = False
        self.spectrum_tex.repeat_y = False
        
        # Runtime states
        self.clock = pygame.time.Clock()
        self.start_time = time.time()
        self.auto_cycle = False
        self.auto_cycle_timer = 0.0
        self.auto_cycle_interval = 16.0
        self.mouse_pos = (0.5, 0.5)
        self.notification_msg = f"Preset {self.current_preset + 1}/{len(self.programs)}: {self.preset_names[self.current_preset]}"
        self.notification_timer = 4.0

    def set_preset(self, index):
        self.current_preset = index % len(self.programs)
        self.current_program = self.programs[self.current_preset]
        self.vao = self.ctx.simple_vertex_array(self.current_program, self.vbo, 'in_vert')
        self.notification_msg = f"Preset {self.current_preset + 1}/{len(self.programs)}: {self.preset_names[self.current_preset]}"
        self.notification_timer = 3.5
        self.last_interaction_time = time.time()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((self.width, self.height), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
            
        new_w, new_h = self.screen.get_size()
        self.handle_resize(new_w, new_h)

    def handle_resize(self, w, h):
        self.width = max(1, w)
        self.height = max(1, h)
        self.ctx.viewport = (0, 0, self.width, self.height)
        self.hud_tex.release()
        self.hud_tex = self.ctx.texture((self.width, self.height), 4)
        self.hud_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)

    def render_hud(self, features, fps):
        """Renders crisp cyberpunk status & controls HUD overlay."""
        self.hud_surface.fill((0, 0, 0, 0))
        
        time_since_interaction = time.time() - self.last_interaction_time
        if not self.show_hud and time_since_interaction > self.hud_timeout and self.notification_timer <= 0:
            return
            
        # Draw translucent top panel
        top_h = 75
        pygame.draw.rect(self.hud_surface, (10, 15, 25, 185), (0, 0, self.width, top_h))
        pygame.draw.line(self.hud_surface, (0, 220, 255, 130), (0, top_h), (self.width, top_h), 2)
        
        # Preset Title
        preset_num = self.current_preset + 1
        if preset_num == 15:
            preset_tag = "[!!! ВООБЩЕ ЖЕСТЬ / ULTIMATE CARNAGE !!!]"
            title_color = (255, 20, 60)
        elif preset_num >= 11:
            preset_tag = "[MEGA HARDCORE]"
            title_color = (255, 140, 20)
        elif preset_num >= 6:
            preset_tag = "[HARDCORE AIMP]"
            title_color = (255, 60, 140)
        else:
            preset_tag = "[PSYCHEDELIC]"
            title_color = (0, 255, 220)

        preset_text = f"[{preset_num}/{len(self.programs)}] {self.preset_names[self.current_preset].upper()} {preset_tag}"
        lbl = self.hud_font_large.render(preset_text, True, title_color)
        self.hud_surface.blit(lbl, (20, 12))
        
        # Audio Mode, Gain & Hardcore status
        audio_src = "DEMO BEAT (Press M to switch)" if self.audio.demo_mode else "SYSTEM AUDIO / BROWSER LOOPBACK"
        hardcore_tag = "ON [ACTIVE]" if self.audio.hardcore else "OFF"
        gain_str = f"SRC: {audio_src}  |  GAIN: {self.audio.gain:.1f}x  |  HARDCORE: {hardcore_tag} (X)  |  FPS: {fps:.0f}"
        lbl_gain = self.hud_font_small.render(gain_str, True, (220, 220, 240))
        self.hud_surface.blit(lbl_gain, (22, 44))
        
        # Energy Bars (Bass, Mid, High, Punch, Strobe) on top-right
        bar_w = 70
        bar_h = 10
        rx = self.width - 440
        
        indicators = [
            ("BASS",   features['bass'] / 2.2,  (255, 50, 100)),
            ("MID",    features['mid'] / 2.2,   (255, 200, 40)),
            ("HIGH",   features['high'] / 2.2,  (50, 220, 255)),
            ("PUNCH",  features['punch'],       (255, 0, 255)),
            ("STROBE", features['strobe'],      (255, 255, 255)),
        ]
        
        for i, (name, val, color) in enumerate(indicators):
            bx = rx + i * (bar_w + 10)
            by = 35
            lbl_b = self.hud_font_small.render(name, True, (180, 180, 190))
            self.hud_surface.blit(lbl_b, (bx, 14))
            
            # Background slot
            pygame.draw.rect(self.hud_surface, (30, 35, 45, 200), (bx, by, bar_w, bar_h), border_radius=3)
            # Filled dynamic bar
            fill_len = int(np.clip(val, 0.0, 1.0) * bar_w)
            if fill_len > 0:
                pygame.draw.rect(self.hud_surface, color, (bx, by, fill_len, bar_h), border_radius=3)
                
        # Bottom controls helper bar
        bot_h = 36
        pygame.draw.rect(self.hud_surface, (10, 15, 25, 180), (0, self.height - bot_h, self.width, bot_h))
        pygame.draw.line(self.hud_surface, (0, 220, 255, 90), (0, self.height - bot_h), (self.width, self.height - bot_h), 1)
        
        help_text = "[1-9, 0, -, =, [, ], \\] Presets (1-15)  |  [Z] Instant CARNAGE (15)  |  [Space] Next  |  [X] Hardcore  |  [F] Fullscreen"
        lbl_help = self.hud_font_small.render(help_text, True, (170, 210, 230))
        self.hud_surface.blit(lbl_help, (20, self.height - bot_h + 9))
        
        # Center notification banner if active
        if self.notification_timer > 0:
            notif_surf = self.hud_font_large.render(self.notification_msg, True, (255, 255, 255))
            nw, nh = notif_surf.get_size()
            cx = (self.width - nw) // 2
            cy = self.height // 2 - 120
            padding = 16
            pygame.draw.rect(self.hud_surface, (0, 0, 0, 210), (cx - padding, cy - padding // 2, nw + padding * 2, nh + padding), border_radius=8)
            border_col = (255, 50, 120) if "HARDCORE" in self.notification_msg or preset_num >= 6 else (0, 255, 200)
            pygame.draw.rect(self.hud_surface, border_col, (cx - padding, cy - padding // 2, nw + padding * 2, nh + padding), width=2, border_radius=8)
            self.hud_surface.blit(notif_surf, (cx, cy))

    def run(self):
        running = True
        
        while running:
            dt = self.clock.tick(60) / 1000.0  # 60 FPS target
            current_time = time.time() - self.start_time
            fps = self.clock.get_fps()
            
            # Decrement notification timer
            if self.notification_timer > 0:
                self.notification_timer -= dt
                
            # Handle Pygame Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    
                elif event.type == pygame.VIDEORESIZE:
                    self.handle_resize(event.w, event.h)
                    
                elif event.type == pygame.MOUSEMOTION:
                    mx, my = event.pos
                    self.mouse_pos = (mx / max(1, self.width), 1.0 - my / max(1, self.height))
                    self.last_interaction_time = time.time()
                    
                elif event.type == pygame.KEYDOWN:
                    self.last_interaction_time = time.time()
                    if event.key in (pygame.K_ESCAPE, pygame.K_q):
                        running = False
                    elif event.key in (pygame.K_f, pygame.K_F11):
                        self.toggle_fullscreen()
                    elif event.key == pygame.K_SPACE or event.key == pygame.K_RIGHT:
                        self.set_preset(self.current_preset + 1)
                    elif event.key == pygame.K_LEFT:
                        self.set_preset(self.current_preset - 1)
                    elif pygame.K_1 <= event.key <= pygame.K_9:
                        self.set_preset(event.key - pygame.K_1)
                    elif event.key == pygame.K_0:
                        self.set_preset(9)   # Preset 10
                    elif event.key == pygame.K_MINUS:
                        self.set_preset(10)  # Preset 11
                    elif event.key == pygame.K_EQUALS:
                        self.set_preset(11)  # Preset 12
                    elif event.key == pygame.K_LEFTBRACKET:
                        self.set_preset(12)  # Preset 13
                    elif event.key == pygame.K_RIGHTBRACKET:
                        self.set_preset(13)  # Preset 14
                    elif event.key in (pygame.K_BACKSLASH, pygame.K_z):
                        self.set_preset(14)  # Preset 15: ВООБЩЕ ЖЕСТЬ
                        self.notification_msg = "[!] TOTAL CARNAGE: ACID GLITCH ENGAGED!"
                        self.notification_timer = 3.5
                    elif event.key == pygame.K_x:
                        self.audio.hardcore = not self.audio.hardcore
                        self.notification_msg = f"HARDCORE AIMP MODE: {'ACTIVATED! 🔥' if self.audio.hardcore else 'DEACTIVATED'}"
                        self.notification_timer = 2.8
                    elif event.key == pygame.K_a:
                        self.auto_cycle = not self.auto_cycle
                        self.notification_msg = f"Auto-Cycle: {'ENABLED' if self.auto_cycle else 'DISABLED'}"
                        self.notification_timer = 2.5
                    elif event.key == pygame.K_m:
                        self.audio.demo_mode = not self.audio.demo_mode
                        self.notification_msg = f"Audio Source: {'DEMO SYNTH' if self.audio.demo_mode else 'SYSTEM LOOPBACK'}"
                        self.notification_timer = 3.0
                    elif event.key == pygame.K_h:
                        self.show_hud = not self.show_hud
                        self.notification_msg = f"HUD: {'VISIBLE' if self.show_hud else 'HIDDEN'}"
                        self.notification_timer = 2.0
                    elif event.key == pygame.K_UP:
                        self.audio.gain = min(6.0, self.audio.gain + 0.2)
                        self.notification_msg = f"Audio Gain: {self.audio.gain:.1f}x"
                        self.notification_timer = 2.0
                    elif event.key == pygame.K_DOWN:
                        self.audio.gain = max(0.2, self.audio.gain - 0.2)
                        self.notification_msg = f"Audio Gain: {self.audio.gain:.1f}x"
                        self.notification_timer = 2.0

            # Auto-cycle presets
            if self.auto_cycle:
                self.auto_cycle_timer += dt
                if self.auto_cycle_timer >= self.auto_cycle_interval:
                    self.auto_cycle_timer = 0.0
                    self.set_preset(self.current_preset + 1)

            # Get real-time audio features
            feats = self.audio.get_features()
            
            # Update 4-channel texture (Spectrum, Waveform, Peak, Punch)
            tex_bytes = np.ascontiguousarray(feats['tex_data'], dtype=np.float32).tobytes()
            self.spectrum_tex.write(tex_bytes)
            self.spectrum_tex.use(location=0)
            
            # Clear framebuffer
            self.ctx.clear(0.0, 0.0, 0.0, 1.0)
            
            # Pass uniforms to active shader
            prog = self.current_program
            safe_set_uniform(prog, 'u_time', float(current_time))
            safe_set_uniform(prog, 'u_resolution', (float(self.width), float(self.height)))
            safe_set_uniform(prog, 'u_mouse', self.mouse_pos)
            safe_set_uniform(prog, 'u_bass', float(feats['bass']))
            safe_set_uniform(prog, 'u_mid', float(feats['mid']))
            safe_set_uniform(prog, 'u_high', float(feats['high']))
            safe_set_uniform(prog, 'u_vol', float(feats['vol']))
            safe_set_uniform(prog, 'u_beat', float(feats['beat']))
            safe_set_uniform(prog, 'u_punch', float(feats['punch']))
            safe_set_uniform(prog, 'u_strobe', float(feats['strobe']))
            safe_set_uniform(prog, 'u_spectrum', 0)
            
            # Render psychedelic / AIMP scene
            self.vao.render(moderngl.TRIANGLES)
            
            # Render HUD overlay
            self.render_hud(feats, fps)
            raw_hud_bytes = pygame.image.tostring(self.hud_surface, 'RGBA', False)
            self.hud_tex.write(raw_hud_bytes)
            self.hud_tex.use(location=1)
            
            self.hud_prog['u_hud_tex'].value = 1
            self.hud_vao.render(moderngl.TRIANGLES)
            
            # Update Window Caption with dynamic metrics
            caption = f"PsychoSound [{self.current_preset+1}/{len(self.programs)}: {self.preset_names[self.current_preset]}] | Gain: {self.audio.gain:.1f}x | FPS: {fps:.0f}"
            pygame.display.set_caption(caption)
            
            pygame.display.flip()
            
        # Cleanup
        self.audio.close()
        pygame.quit()
        sys.exit(0)

if __name__ == '__main__':
    app = PsychoVisualizerApp()
    app.run()
