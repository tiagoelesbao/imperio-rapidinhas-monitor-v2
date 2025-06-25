import sys
from pathlib import Path

# Adiciona diretorio ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from capture_complete import ImperioRapidinhasFinal
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent / 'legacy'))
    from capture_legacy import ImperioRapidinhasFinal

class CaptureService:
    def __init__(self):
        self.config_file = './config/config.json'

    def full_capture(self, headless=False):
        capture = ImperioRapidinhasFinal(self.config_file)
        capture.run(headless=headless, capture_reports=True)

    def quick_capture(self, headless=False):
        capture = ImperioRapidinhasFinal(self.config_file)
        capture.run(headless=headless, capture_reports=False)
