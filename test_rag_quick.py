#!/usr/bin/env python
"""Quick test of RAG pipeline with PDF documents"""

import json
from backend.agents.clinician_rag import generate_medical_guidelines

# Test with simple diabetes profile
profile = {
    'age': 50,
    'conditions': ['type 2 diabetes'],
    'bmi': 30,
    'activity_level': 'sedentary'
}

print('=' * 80)
print('Testing RAG Medical Engine with Document Loading')
print('=' * 80)
print()

try:
    result = generate_medical_guidelines(profile)
    
    print(f'✓ Confidence: {result["confidence"]:.2%}')
    print(f'✓ Guidelines found: {len(result["guidelines"])}')
    print(f'✓ Risk factors identified: {len(result["global_risks"])}')
    print(f'✓ Safety warnings: {len(result["safety_warnings"])}')
    
    if result['guidelines']:
        print(f'\nFirst guideline:')
        g = result['guidelines'][0]
        print(f'  • Condition: {g["condition"]}')
        print(f'  • Exercises: {", ".join(g["recommended_exercises"][:2])}')
        print(f'  • Source: {g["source"]}')
        print(f'  • Contraindications: {len(g["contraindications"])} listed')
        print(f'  • Precautions: {len(g["precautions"])} listed')
    
    print(f'\n✅ SUCCESS! RAG pipeline is working with documents.')
    
except Exception as e:
    print(f'❌ ERROR: {e}')
    import traceback
    traceback.print_exc()
