import subprocess
import json

# Try searching for metabolic studies
r = subprocess.run(
    ['C:\\Users\\User\\Desktop\\agentic\\workflow_codex\\tools\\tool43CA\\.venv\\Scripts\\threeca.exe', 'search', 'metabolic'],
    capture_output=True, text=True
)
print('=== METABOLIC SEARCH ===')
print('RC:', r.returncode)
print('STDOUT:', r.stdout[:5000])
print('STDERR:', r.stderr[:2000])

# Try broad search
r2 = subprocess.run(
    ['C:\\Users\\User\\Desktop\\agentic\\workflow_codex\\tools\\tool43CA\\.venv\\Scripts\\threeca.exe', 'search', ''],
    capture_output=True, text=True
)
print('\n=== BROAD SEARCH ===')
print('RC:', r2.returncode)
data = json.loads(r2.stdout)
print('Total studies:', data['count'])
for s in data['studies'][:30]:
    print(f"  {s['id']} {s['title']} {s['category']} {s['disease']} {s['technology']}")

# Try searching for energy
r3 = subprocess.run(
    ['C:\\Users\\User\\Desktop\\agentic\\workflow_codex\\tools\\tool43CA\\.venv\\Scripts\\threeca.exe', 'search', 'energy'],
    capture_output=True, text=True
)
print('\n=== ENERGY SEARCH ===')
print('RC:', r3.returncode)
print('STDOUT:', r3.stdout[:5000])

# Try searching for glycolysis
r4 = subprocess.run(
    ['C:\\Users\\User\\Desktop\\agentic\\workflow_codex\\tools\\tool43CA\\.venv\\Scripts\\threeca.exe', 'search', 'glycolysis'],
    capture_output=True, text=True
)
print('\n=== GLYCOLYSIS SEARCH ===')
print('RC:', r4.returncode)
print('STDOUT:', r4.stdout[:5000])

# Try searching for oxidative phosphorylation
r5 = subprocess.run(
    ['C:\\Users\\User\\Desktop\\agentic\\workflow_codex\\tools\\tool43CA\\.venv\\Scripts\\threeca.exe', 'search', 'oxidative phosphorylation'],
    capture_output=True, text=True
)
print('\n=== OXIDATIVE PHOSPHORYLATION SEARCH ===')
print('RC:', r5.returncode)
print('STDOUT:', r5.stdout[:5000])
