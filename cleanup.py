"""
CLEANUP SCRIPT - Organize files for team push
Creates docs/ folder and moves documentation
"""

import os
import shutil
from pathlib import Path

# Define paths
project_root = Path(r'C:\Users\dell\PycharmProjects\AI4SDG-Challenge')
docs_dir = project_root / 'docs'

# Create docs folder if not exists
docs_dir.mkdir(exist_ok=True)

# Files to move to docs/
docs_files = [
    'README_ML_MODULE.md',
    'INTEGRATION_GUIDE.md',
    'QUICK_INPUT_REFERENCE.md',
    'DEPLOYMENT_GUIDE.md',
]

# Files to DELETE (redundant)
delete_files = [
    'START_HERE.md',
    'TAHA_FINAL_SUMMARY.md',
    'TAHA_COMPLETE_SUBMISSION.md',
    'ML_COMPLETION_SUMMARY.md',
    'ML_MODULE_STATUS.md',
    'FILE_INDEX.md',
    'COMPLETE_INDEX.md',
    'INPUTS_GUIDE.md',
    'HACKATHON_CHECKLIST.md',
    'PROJECT_STRUCTURE.py',
    'TEST_RESULTS.md',
    'demo_ml_pipeline.py',
    'simple_test.py',
    'show_outputs.py',
]

print("\n" + "="*80)
print("🧹 CLEANUP SCRIPT - Organizing files for team push")
print("="*80)

# Move documentation files to docs/
print("\n📁 Moving documentation to docs/ folder...")
for file in docs_files:
    src = project_root / file
    dst = docs_dir / file
    if src.exists():
        shutil.move(str(src), str(dst))
        print(f"   ✅ Moved: {file} → docs/")
    else:
        print(f"   ⚠️  Not found: {file}")

# Delete redundant files
print("\n🗑️  Deleting redundant files...")
for file in delete_files:
    path = project_root / file
    if path.exists():
        os.remove(path)
        print(f"   ✅ Deleted: {file}")
    else:
        print(f"   ⚠️  Not found: {file}")

print("\n" + "="*80)
print("✅ CLEANUP COMPLETE!")
print("="*80)

print("\n📂 PROJECT STRUCTURE (CLEAN):")
print("""
AI4SDG-Challenge/
├── README.md                    ✅ Main documentation
├── requirements.txt             ✅ Dependencies
├── .env.example                 ✅ Environment
│
├── backend/
│   ├── ml/                      ✅ Core ML module
│   │   ├── contracts.py
│   │   ├── sentiment_analysis.py
│   │   ├── risk_model.py
│   │   ├── pipeline.py
│   │   ├── config.py
│   │   ├── ml_routes.py
│   │   └── test_ml.py
│   └── api/
│       └── ml_routes.py
│
├── docs/                        ✅ Documentation (organized)
│   ├── README_ML_MODULE.md
│   ├── INTEGRATION_GUIDE.md
│   ├── QUICK_INPUT_REFERENCE.md
│   └── DEPLOYMENT_GUIDE.md
│
├── 🧪 TESTS
│   ├── direct_test.py
│   ├── test_ml_comprehensive.py
│   └── verify_setup.py
│
└── 🛠️ UTILITIES
    ├── input_builder.py
    └── FINAL_STRUCTURE.md
""")

print("\n🚀 READY TO PUSH TO TEAM!")
print("="*80)

