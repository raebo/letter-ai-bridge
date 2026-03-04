import sys
import os

print("="*60)
print("PYTHON ENVIRONMENT DIAGNOSE")
print("="*60)

# 1. Welches Python wird wirklich ausgeführt?
print(f"INTERPRETER: {sys.executable}")

# 2. Die Suchpfade - hier liegt meist das Problem
print("\nSUCHPFADE (sys.path):")
for path in sys.path:
    if path: 
        print(f" - {path}")

print("\n" + "="*60)
print("PAKET-TESTS:")

# 3. Test: torch (für die RTX 3080)
try:
    import torch
    print(f"[OK] torch gefunden: {torch.__file__}")
    print(f"     CUDA (GPU) verfügbar: {torch.cuda.is_available()}")
except ImportError:
    print("[!!] torch fehlt")

# 4. Test: transformers (der Problemkandidat)
try:
    import transformers
    print(f"[OK] transformers gefunden: {transformers.__file__}")
    from transformers import BertModel
    print("[OK] BertModel erfolgreich geladen.")
except ImportError:
    print("[!!] transformers fehlt")
except Exception as e:
    print(f"[!!] FEHLER beim Laden von transformers: {e}")

print("="*60)
