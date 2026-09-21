from pathlib import Path
def test_structure(): assert Path('app/api').exists() and Path('app/models').exists() and Path('app/services').exists()