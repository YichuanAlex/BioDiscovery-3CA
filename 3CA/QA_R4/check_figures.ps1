# Check figures directory contents
Get-ChildItem -Path "figures" -Recurse -File -ErrorAction SilentlyContinue | Select-Object FullName, Length, LastWriteTime
Get-ChildItem -Path "figures\cd8_analysis" -Recurse -File -ErrorAction SilentlyContinue | Select-Object FullName, Length, LastWriteTime
