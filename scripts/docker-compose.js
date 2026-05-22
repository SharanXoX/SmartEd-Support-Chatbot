/**
 * Runs `docker compose` even when Docker Desktop's bin folder is not on PATH
 * (common in Cursor / some PowerShell sessions on Windows).
 */
const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..");

function resolveDockerBin() {
  if (process.platform === "win32") {
    const candidates = [
      path.join(
        process.env.ProgramFiles || "C:\\Program Files",
        "Docker",
        "Docker",
        "resources",
        "bin",
        "docker.exe",
      ),
      "C:\\Program Files\\Docker\\Docker\\resources\\bin\\docker.exe",
    ];
    for (const p of candidates) {
      if (fs.existsSync(p)) return p;
    }
  }
  return "docker";
}

const docker = resolveDockerBin();
const args = ["compose", ...process.argv.slice(2)];

const result = spawnSync(docker, args, {
  cwd: repoRoot,
  stdio: "inherit",
  env: process.env,
  shell: false,
});

if (result.error) {
  console.error(
    "\nDocker failed to start. If Docker Desktop shows 'Engine running' but this script cannot find docker:",
  );
  console.error("  1. Open Docker Desktop → Settings → Advanced → enable CLI / PATH integration");
  console.error("  2. Or run: scripts\\start-docker.bat");
  console.error(`  3. Expected docker at: ${docker}\n`);
  console.error(result.error.message);
  process.exit(1);
}

process.exit(result.status ?? 1);
