from pathlib import Path

# Główny katalog projektu
BASE_DIR = Path(__file__).resolve().parent

# Foldery
TEMPLATES_DIR = BASE_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
LOGS_DIR = BASE_DIR / "logs"

# Tworzenie folderów, jeśli nie istnieją
for folder in (TEMPLATES_DIR, OUTPUT_DIR, LOGS_DIR):
    folder.mkdir(exist_ok=True)

# Nazwa pliku wynikowego
OUTPUT_FILENAME = "specyfikacja_wypelniona.xlsx"

# Obsługiwane rozszerzenia
SUPPORTED_EXTENSIONS = (".xlsx", ".xls")