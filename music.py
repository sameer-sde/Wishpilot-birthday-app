from pathlib import Path

try:
    import pygame
except Exception:
    pygame = None


class MusicPlayer:
    def __init__(self, logger):
        self.logger = logger
        self.is_playing = False
        self.initialized = False
        self.current_path = None

    def _init(self):
        if pygame is None:
            raise RuntimeError("pygame is not installed. Music feature is unavailable.")

        if not self.initialized:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.initialized = True

    def play(self, path):
        if not path:
            raise ValueError("Music file path is empty.")

        music_path = Path(path).expanduser().resolve()

        if not music_path.exists():
            raise FileNotFoundError(f"Music file not found: {music_path}")
        if not music_path.is_file():
            raise ValueError(f"Music path is not a file: {music_path}")

        self._init()

        pygame.mixer.music.load(str(music_path))
        pygame.mixer.music.play(-1)
        self.is_playing = True
        self.current_path = str(music_path)
        self.logger(f"Playing music: {music_path}")

    def stop(self):
        if pygame and self.initialized:
            pygame.mixer.music.stop()
            try:
                pygame.mixer.music.unload()
            except Exception:
                pass

        self.is_playing = False
        self.current_path = None
        self.logger("Music stopped.")