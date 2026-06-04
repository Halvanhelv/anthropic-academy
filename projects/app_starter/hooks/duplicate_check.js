const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

process.stdin.setEncoding("utf8");
let input = "";
process.stdin.on("data", (d) => (input += d));
process.stdin.on("end", () => {
  const toolArgs = JSON.parse(input);
  const filePath = toolArgs.tool_input?.file_path || toolArgs.tool_input?.file || "";

  let toolsDir = path.join(process.cwd(), "tools");
  if (!fs.existsSync(toolsDir)) {
    toolsDir = path.join(process.cwd(), "projects", "app_starter", "tools");
  }
  if (!fs.existsSync(toolsDir) || !filePath.includes("/tools/")) {
    process.exit(0);
  }

  try {
    const editedFile = path.basename(filePath);
    const newFuncs = execSync(
      `grep -n "^def \\|^async def " "${filePath}"`,
      { encoding: "utf8" }
    ).trim().split("\n").map(line => {
      const match = line.match(/^\d+:\s*(?:async )?def (\w+)/);
      return match ? match[1] : null;
    }).filter(Boolean);

    const allFuncs = execSync(
      `grep -rn "^def \\|^async def " "${toolsDir}" --include="*.py"`,
      { encoding: "utf8" }
    ).trim().split("\n");

    const duplicates = [];
    for (const funcName of newFuncs) {
      const locations = allFuncs
        .filter(line => line.includes(`def ${funcName}`))
        .map(line => {
          const match = line.match(/^(.+?):(\d+):/);
          return match ? `${path.basename(match[1])}:${match[2]}` : null;
        })
        .filter(Boolean);

      if (locations.length > 1) {
        duplicates.push(`  "${funcName}" found in: ${locations.join(", ")}`);
      }
    }

    if (duplicates.length > 0) {
      const prompt = `Duplicate functions detected in tools/:\n${duplicates.join("\n")}\nReview and use existing functions instead of duplicates.`;
      try {
        const result = execSync(
          `claude -p "You are reviewing tools/ directory for duplicate functions. ${prompt.replace(/"/g, '\\"')} Suggest which duplicate to remove and which to keep."`,
          { encoding: "utf8", timeout: 60000 }
        );
        console.error(`AI Review:\n${result.trim()}`);
      } catch (e) {
        console.error(prompt);
      }
    }
  } catch (e) {
    // no functions found or error — fine
  }

  process.exit(0);
});
