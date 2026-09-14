import subprocess, json, sys

threeca = r"C:\Users\User\Desktop\agentic\workflow_codex\tools\tool43CA\.venv\Scripts\threeca.exe"

# Test basic execution
r = subprocess.run([threeca, "--version"], capture_output=True, text=True, timeout=10)
print("Version:", r.stdout.strip())

# Test search for metabolic
r2 = subprocess.run([threeca, "search", "metabolic"], capture_output=True, text=True, timeout=30)
print("Search metabolic RC:", r2.returncode)
print("Search metabolic STDOUT:", r2.stdout[:2000])
print("Search metabolic STDERR:", r2.stderr[:1000])

# Test search for all
r3 = subprocess.run([threeca, "search", ""], capture_output=True, text=True, timeout=30)
print("Search all RC:", r3.returncode)
data = json.loads(r3.stdout)
print("Total studies:", data["count"])
