"use strict";

import fs from "node:fs";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { fileURLToPath, pathToFileURL } from "node:url";

const workspace = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "..");
// Keep the Windows helper's policy handshake inside this workflow. The helper
// launches CODEX_CLI_PATH app-server; never let that lookup fall back to a
// system-installed Codex binary.
const isolatedEnvironment = {
  CODEX_HOME: path.join(workspace, ".runtime", "codex-home"),
  CODEX_CLI_PATH: path.join(workspace, "codex-local.cmd"),
  THREECA_CACHE: path.join(workspace, ".threeca", "cache"),
  PYTHONNOUSERSITE: "1",
  NODE_REPL_DISABLE_ANALYTICS: "1",
  BROWSER_USE_DISABLE_AMBIENT_NETWORK: "1",
};
for (const [name, value] of Object.entries(isolatedEnvironment)) process.env[name] = value;
const skyEntry = path.join(
  workspace,
  "tools",
  "computer-use",
  "node_modules",
  "@oai",
  "sky",
  "dist",
  "project",
  "cua",
  "sky_js",
  "src",
  "index.js",
);
const captures = path.join(workspace, "tools", "computer-use", "captures");
const forbiddenApp = /(codex|chatgpt|powershell|cmd\.exe|terminal|visual studio|\btrae\b|credential|password|security)/i;
const forbiddenKey = /(^|\+)(meta|windows|win|cmd|command|super|os)(\+|$)/i;
const observations = new Map();
const returnedWindows = new Map();
const approvedComputerUseRequests = new Set();
let client;

export function createComputerUseTools(functionTool, confirm) {
  return {
    definitions: [functionTool(
      "computer_use",
      "Control an allowed Windows app. First list_apps, then use an exact returned app and window_id. Observe before and after each action. The user must approve access to an app when prompted.",
      {
        action: {
          type: "string",
          enum: ["list_apps", "list_windows", "launch_app", "get_window_state", "click", "press_key", "type_text", "scroll", "set_value", "drag", "secondary_action", "activate_window"],
        },
        app: { type: "string", description: "Exact app id returned by list_apps, or an executable path for launch_app" },
        window_id: { type: "integer", minimum: 0 },
        include_screenshot: { type: "boolean" },
        include_text: { type: "boolean" },
        element_index: { type: "integer", minimum: 0 },
        x: { type: "integer" },
        y: { type: "integer" },
        to_x: { type: "integer" },
        to_y: { type: "integer" },
        scroll_x: { type: "integer" },
        scroll_y: { type: "integer" },
        key: { type: "string" },
        text: { type: "string" },
        value: { type: "string" },
        secondary_action: { type: "string" },
        click_count: { type: "integer", minimum: 1, maximum: 3 },
        mouse_button: { type: "string", enum: ["left", "right", "middle"] },
        screenshot_id: { type: "string", description: "Screenshot id from the latest observation; required for coordinate actions" },
      },
      ["action"],
    )],
    execute: (args) => execute(args, confirm),
  };
}

async function getClient(confirm) {
  if (!fs.existsSync(skyEntry)) throw new Error(`Computer Use runtime is missing: ${skyEntry}`);
  if (!client) {
    const imported = await import(pathToFileURL(skyEntry).href);
    client = imported.sky;
  }
  globalThis.nodeRepl ||= {};
  globalThis.nodeRepl.config ||= {};
  globalThis.nodeRepl.createElicitation = async ({ message }) => {
    if (approvedComputerUseRequests.has(message)) return { action: "accept" };
    const approved = await confirm(message);
    if (approved) approvedComputerUseRequests.add(message);
    return { action: approved ? "accept" : "decline" };
  };
  globalThis.nodeRepl.emitImage ||= async () => {};
  return client;
}

function assertAllowed(value) {
  const identity = `${value.app || ""} ${value.title || ""}`;
  if (forbiddenApp.test(identity)) throw new Error(`Computer Use is blocked for this app: ${identity.trim()}`);
}

function windowKey(window) {
  return `${window.app}:${window.id}`;
}

async function selectedWindow(sky, args) {
  const hasWindowId = Number.isInteger(Number(args.window_id));
  if (!hasWindowId) {
    const observed = [...observations.values()];
    if (observed.length !== 1) {
      throw new Error("window_id from list_apps or list_windows is required unless exactly one window was just observed.");
    }
    const window = observed[0].window;
    assertAllowed(window);
    return window;
  }
  const id = Number(args.window_id);
  const candidates = [...returnedWindows.values()].filter((window) => window.id === id);
  if (candidates.length !== 1) {
    throw new Error("The window_id must identify exactly one window returned by the latest list_apps or list_windows call.");
  }
  const returned = candidates[0];
  const window = await sky.get_window({ app: returned.app, id: returned.id });
  assertAllowed(window);
  return window;
}

function rememberApps(apps) {
  returnedWindows.clear();
  for (const app of apps) {
    for (const window of app.windows || []) {
      if (Number.isInteger(window.id) && typeof window.app === "string" && window.app) {
        returnedWindows.set(`${window.app}:${window.id}`, window);
      }
    }
  }
}

function rememberWindows(windows) {
  returnedWindows.clear();
  for (const window of windows) {
    if (Number.isInteger(window.id) && typeof window.app === "string" && window.app) {
      returnedWindows.set(`${window.app}:${window.id}`, window);
    }
  }
}

function saveScreenshots(screenshots) {
  if (!screenshots.length) return [];
  fs.mkdirSync(captures, { recursive: true });
  const captureId = `${Date.now()}-${randomUUID().slice(0, 12)}`;
  return screenshots.map((screenshot, index) => {
    const match = /^data:image\/([A-Za-z0-9.+-]+);base64,([\s\S]+)$/.exec(String(screenshot.url || ""));
    if (!match) return { ...screenshot, url: "omitted: unsupported image encoding" };
    const extension = (match[1].toLowerCase() === "jpeg" ? "jpg" : match[1].toLowerCase()).replace(/[^a-z0-9]/g, "") || "img";
    const file = path.join(captures, `capture-${captureId}-${index}.${extension}`);
    fs.writeFileSync(file, Buffer.from(match[2], "base64"));
    return {
      id: screenshot.id,
      path: file,
      width: screenshot.width,
      height: screenshot.height,
      originX: screenshot.originX,
      originY: screenshot.originY,
      zIndex: screenshot.zIndex,
    };
  });
}

async function observe(sky, window, includeScreenshot = false, includeText = true) {
  const state = await sky.get_window_state({
    window,
    include_screenshot: includeScreenshot,
    include_text: includeText,
  });
  return {
    window: state.window,
    accessibility: state.accessibility && {
      ...state.accessibility,
      tree: state.accessibility.tree.slice(0, 40000),
      document_text: state.accessibility.document_text?.slice(0, 20000),
    },
    screenshots: saveScreenshots(state.screenshots),
  };
}

async function execute(args, confirm) {
  const sky = await getClient(confirm);
  const action = args.action;
  if (action === "list_apps") {
    const apps = await sky.list_apps();
    observations.clear();
    rememberApps(apps);
    return JSON.stringify(apps);
  }
  if (action === "list_windows") {
    const windows = await sky.list_windows();
    observations.clear();
    rememberWindows(windows);
    return JSON.stringify(windows);
  }
  if (action === "launch_app") {
    if (!args.app) throw new Error("app is required for launch_app.");
    assertAllowed({ app: args.app });
    if (!await confirm(`Allow Computer Use to launch ${args.app}?`)) throw new Error("Computer Use action declined by user.");
    await sky.launch_app({ app: args.app });
    const apps = await sky.list_apps();
    rememberApps(apps);
    return JSON.stringify(apps.filter((app) => app.id === args.app || app.windows.length));
  }

  const window = await selectedWindow(sky, args);
  const key = windowKey(window);
  if (action === "get_window_state") {
    const state = await observe(sky, window, args.include_screenshot !== false, args.include_text !== false);
    observations.set(key, state);
    return JSON.stringify(state);
  }

  const observation = observations.get(key);
  if (!observation) throw new Error("Observe this exact window with get_window_state before acting.");
  const actionWindow = observation.window;
  assertAllowed(actionWindow);
  if (!await confirm(`Allow Computer Use action '${action}' in '${window.title || window.app}'?`)) {
    throw new Error("Computer Use action declined by user.");
  }
  observations.delete(key);
  if (["click", "scroll", "drag"].includes(action) && args.element_index === undefined) {
    const latestScreenshot = observation.screenshots[0]?.id;
    if (!args.screenshot_id || args.screenshot_id !== latestScreenshot) {
      throw new Error("A matching screenshot_id from the latest observation is required for coordinate actions.");
    }
  }

  if (action === "click") {
    await sky.click({ window: actionWindow, element_index: args.element_index, x: args.x, y: args.y, screenshotId: args.screenshot_id, click_count: args.click_count, mouse_button: args.mouse_button });
  } else if (action === "press_key") {
    if (!args.key || forbiddenKey.test(args.key.replace(/\s+/g, ""))) throw new Error("Windows-key shortcuts are blocked.");
    await sky.press_key({ window: actionWindow, key: args.key });
  } else if (action === "type_text") {
    await sky.type_text({ window: actionWindow, text: args.text });
  } else if (action === "scroll") {
    await sky.scroll({ window: actionWindow, x: args.x, y: args.y, screenshotId: args.screenshot_id, scrollX: args.scroll_x, scrollY: args.scroll_y });
  } else if (action === "set_value") {
    await sky.set_value({ window: actionWindow, element_index: args.element_index, value: args.value });
  } else if (action === "drag") {
    await sky.drag({ window: actionWindow, from_x: args.x, from_y: args.y, to_x: args.to_x, to_y: args.to_y, screenshotId: args.screenshot_id });
  } else if (action === "secondary_action") {
    await sky.perform_secondary_action({ window: actionWindow, element_index: args.element_index, action: args.secondary_action });
  } else if (action === "activate_window") {
    await sky.activate_window({ window: actionWindow });
  } else {
    throw new Error(`Unsupported Computer Use action: ${action}`);
  }

  try {
    const after = await observe(sky, actionWindow);
    observations.set(key, after);
    return JSON.stringify({ ok: true, after });
  } catch (error) {
    return JSON.stringify({ ok: true, after: { unavailable: error.message } });
  }
}
