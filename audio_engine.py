"""
Audio Engine: Captures system/browser loopback audio on Windows using WASAPI
and computes real-time FFT spectrum, oscilloscope waveform, bass, mid, high,
punch, and strobe dynamics like classic Winamp/AIMP visualizers.
"""

import time
import threading
import numpy as np
import soundcard as sc

class AudioAnalyzer:
    def __init__(self, sample_rate=44100, buffer_size=2048, num_bands=64):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.num_bands = num_bands
        
        # Audio buffer and lock
        self._lock = threading.Lock()
        self._raw_buffer = np.zeros(self.buffer_size, dtype=np.float32)
        self._is_running = True
        self.demo_mode = False
        self.gain = 1.8  # User adjustable gain multiplier
        self.hardcore = False  # Hardcore AIMP aggressive mode
        
        # Dynamics
        self.smooth_bass = 0.0
        self.smooth_mid = 0.0
        self.smooth_high = 0.0
        self.smooth_vol = 0.0
        self.beat_impulse = 0.0
        self.punch = 0.0
        self.strobe = 0.0
        self.prev_bass = 0.0
        
        self.spectrum_smooth = np.zeros(self.num_bands, dtype=np.float32)
        self.spectrum_raw = np.zeros(self.num_bands, dtype=np.float32)
        self.waveform_norm = np.zeros(self.num_bands, dtype=np.float32)
        
        # Precompute FFT frequency bins (logarithmic spacing: 20Hz - 16000Hz)
        freqs = np.fft.rfftfreq(self.buffer_size, 1.0 / self.sample_rate)
        log_edges = np.logspace(np.log10(20), np.log10(min(16000, self.sample_rate // 2)), self.num_bands + 1)
        self.band_indices = []
        for i in range(self.num_bands):
            idx = np.where((freqs >= log_edges[i]) & (freqs < log_edges[i + 1]))[0]
            if len(idx) == 0:
                closest = np.argmin(np.abs(freqs - log_edges[i]))
                idx = np.array([closest])
            self.band_indices.append(idx)
            
        self.window = np.hanning(self.buffer_size)
        
        # Start capture thread
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _capture_loop(self):
        """Continuously captures system loopback audio via soundcard."""
        while self._is_running:
            if self.demo_mode:
                self._generate_demo_chunk()
                time.sleep(self.buffer_size / self.sample_rate * 0.8)
                continue

            try:
                speaker = sc.default_speaker()
                loopback = sc.get_microphone(id=str(speaker.name), include_loopback=True)
                with loopback.recorder(samplerate=self.sample_rate, blocksize=self.buffer_size) as rec:
                    while self._is_running and not self.demo_mode:
                        chunk = rec.record(numframes=self.buffer_size)
                        if chunk.ndim > 1 and chunk.shape[1] > 1:
                            mono = np.mean(chunk, axis=1)
                        else:
                            mono = chunk.flatten()
                            
                        with self._lock:
                            self._raw_buffer = mono.astype(np.float32)
            except Exception:
                time.sleep(0.5)

    def _generate_demo_chunk(self):
        """Generates punchy hard-hitting electronic beats for testing."""
        t = time.time()
        phase = t * 2.0 * np.pi
        
        # Heavy club kick (132 BPM)
        bpm = 132.0
        beat_period = 60.0 / bpm
        beat_phase = (t % beat_period) / beat_period
        
        # Hard kick punch
        kick_freq = 60.0 * (1.0 + 4.0 * np.exp(-beat_phase * 28.0))
        kick = np.exp(-beat_phase * 12.0) * np.sin(2.0 * np.pi * kick_freq * beat_phase)
        
        # Sizzling hi-hat
        hat_phase = (t % (beat_period / 4.0)) / (beat_period / 4.0)
        noise = (np.random.rand(self.buffer_size) - 0.5) * np.exp(-hat_phase * 30.0) * 0.5
        
        # Acid synthline
        t_arr = np.linspace(0, self.buffer_size / self.sample_rate, self.buffer_size)
        synth = 0.35 * np.sin(2 * np.pi * 130.0 * t_arr + np.sin(phase * 1.5)) + 0.2 * np.sin(2 * np.pi * 260.0 * t_arr)
        
        mono = kick * 1.0 + noise + synth
        with self._lock:
            self._raw_buffer = mono.astype(np.float32)

    def get_features(self):
        """Processes current audio buffer and returns dynamic visualizer features."""
        with self._lock:
            audio = self._raw_buffer.copy()
            
        if len(audio) < self.buffer_size:
            audio = np.pad(audio, (0, self.buffer_size - len(audio)))
            
        eff_gain = self.gain * (1.5 if self.hardcore else 1.0)
        
        # Compute RMS volume
        raw_vol = np.sqrt(np.mean(audio ** 2) + 1e-9) * eff_gain
        
        # Windowed FFT
        windowed = audio * self.window
        fft_complex = np.fft.rfft(windowed)
        magnitude = (np.abs(fft_complex) / (self.buffer_size / 2)) * eff_gain
        
        # Compute log-band spectrum
        spectrum = np.zeros(self.num_bands, dtype=np.float32)
        for i, idx in enumerate(self.band_indices):
            spectrum[i] = np.mean(magnitude[idx])
            
        # Boost highs and sub-bass slightly for visual punch
        boost = np.linspace(1.2, 3.2, self.num_bands)
        self.spectrum_raw = np.clip(spectrum * boost, 0.0, 2.0)
        
        # Fast attack, smooth decay
        alpha_attack = 0.75 if self.hardcore else 0.65
        alpha_decay = 0.30 if self.hardcore else 0.22
        for i in range(self.num_bands):
            if self.spectrum_raw[i] > self.spectrum_smooth[i]:
                self.spectrum_smooth[i] = (1 - alpha_attack) * self.spectrum_smooth[i] + alpha_attack * self.spectrum_raw[i]
            else:
                self.spectrum_smooth[i] = (1 - alpha_decay) * self.spectrum_smooth[i] + alpha_decay * self.spectrum_raw[i]
                
        # Split frequency bands
        n = self.num_bands
        b_end = int(n * 0.18)
        m_end = int(n * 0.60)
        
        raw_bass = float(np.mean(self.spectrum_smooth[:b_end])) * 2.4
        raw_mid  = float(np.mean(self.spectrum_smooth[b_end:m_end])) * 1.9
        raw_high = float(np.mean(self.spectrum_smooth[m_end:])) * 2.6
        
        # Hardcore kick/beat detection
        bass_diff = max(0.0, raw_bass - self.prev_bass)
        self.prev_bass = raw_bass
        
        # Strobe and punch triggers on sharp kicks
        kick_threshold = 0.06 if self.hardcore else 0.09
        if bass_diff > kick_threshold and raw_bass > 0.12:
            self.beat_impulse = min(1.0, self.beat_impulse + bass_diff * 4.5)
            self.punch = min(1.0, max(self.punch, bass_diff * 3.5))
            if bass_diff > 0.14 or raw_bass > 0.5:
                self.strobe = 1.0
        else:
            self.beat_impulse *= 0.85
            self.punch *= 0.80
            self.strobe *= 0.72
            
        # Exponential moving averages for baseline flow
        self.smooth_bass = 0.65 * self.smooth_bass + 0.35 * raw_bass
        self.smooth_mid  = 0.70 * self.smooth_mid  + 0.30 * raw_mid
        self.smooth_high = 0.70 * self.smooth_high + 0.30 * raw_high
        self.smooth_vol  = 0.75 * self.smooth_vol  + 0.25 * raw_vol
        
        # Time-domain waveform downsampled to num_bands for oscilloscope
        wave_indices = np.linspace(0, len(audio) - 1, self.num_bands).astype(int)
        self.waveform_norm = np.clip(audio[wave_indices] * eff_gain * 1.2, -1.0, 1.0)
        
        # Pack 4-channel texture data:
        # R: Smoothed Spectrum [0..1]
        # G: Normalized Waveform [-1..1]
        # B: Raw Peak Spectrum [0..2]
        # A: Beat Punch
        tex_data = np.zeros((1, self.num_bands, 4), dtype=np.float32)
        tex_data[0, :, 0] = self.spectrum_smooth
        tex_data[0, :, 1] = self.waveform_norm
        tex_data[0, :, 2] = self.spectrum_raw
        tex_data[0, :, 3] = self.punch
        
        return {
            'bass': float(np.clip(self.smooth_bass, 0.0, 3.0)),
            'mid': float(np.clip(self.smooth_mid, 0.0, 3.0)),
            'high': float(np.clip(self.smooth_high, 0.0, 3.0)),
            'vol': float(np.clip(self.smooth_vol, 0.0, 2.5)),
            'beat': float(np.clip(self.beat_impulse, 0.0, 1.0)),
            'punch': float(np.clip(self.punch, 0.0, 1.0)),
            'strobe': float(np.clip(self.strobe, 0.0, 1.0)),
            'tex_data': tex_data
        }

    def close(self):
        self._is_running = False
