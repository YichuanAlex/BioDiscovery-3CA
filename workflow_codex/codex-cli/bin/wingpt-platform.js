import path from "node:path";

export const isWindows = process.platform === "win32";
export const shellToolName = isWindows ? "run_powershell" : "run_shell";
export const shellInstructions = isWindows
  ? "The host shell is Windows PowerShell 5.1. Use PowerShell syntax and propagate native exit codes."
  : "The host shell is /bin/bash on macOS/Linux. Use POSIX paths and Bash syntax. Use the scientific Python path below for Python commands; never use PowerShell commands or Windows drive paths.";

export function scientificPython(root) {
  return process.env.WINGPT_PYTHON || (isWindows
    ? path.join(root, "tools", "tool43CA", ".venv", "Scripts", "python.exe")
    : path.join(root, ".runtime", "macos", "python", "bin", "python"));
}

export function shellInvocation(command) {
  if (!isWindows) return { executable: "/bin/bash", args: ["-e", "-o", "pipefail", "-c", command] };
  const executable = path.join(process.env.SystemRoot || "C:\\Windows", "System32", "WindowsPowerShell", "v1.0", "powershell.exe");
  const wrapped = `$ErrorActionPreference = 'Stop'; [Console]::OutputEncoding = [Text.UTF8Encoding]::new(); $OutputEncoding = [Console]::OutputEncoding;\n${command}\nif ($null -ne $LASTEXITCODE) { exit $LASTEXITCODE }`;
  return { executable, args: ["-NoProfile", "-EncodedCommand", Buffer.from(wrapped, "utf16le").toString("base64")] };
}
