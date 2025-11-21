-- PoB bridge: run PoB headless with a build XML on stdin and emit JSON stats.
-- Usage: luajit pob_bridge.lua /path/to/Path\ of\ Building.exe
--
-- Minimal, non-blocking: on any failure, prints '{}' and exits 0 so callers can
-- fall back to lightweight parsing without breaking workflows.

local json = require("json")  -- provided by PoB bundled Lua modules
local lfs = require("lfs")    -- provided with PoB

local exe_path = arg[1]
if not exe_path or exe_path == "" then
  io.write("{}")
  os.exit(0)
end

local function read_stdin()
  local chunks = {}
  for line in io.lines() do
    table.insert(chunks, line)
  end
  return table.concat(chunks, "\\n")
end

local function safe_call(fn, ...)
  local ok, res = pcall(fn, ...)
  if not ok then
    return nil
  end
  return res
end

local function main()
  local xml = read_stdin()
  if xml == "" then
    io.write("{}")
    return
  end

  local pob = safe_call(require, "PathOfBuilding")
  if not pob then
    io.write("{}")
    return
  end

  -- PoB expects to run from its install dir for data paths
  local exe_dir = exe_path:match("^(.*)[/\\\\][^/\\\\]+$") or "."
  lfs.chdir(exe_dir)

  local build = pob.NewBuild()
  if not build then
    io.write("{}")
    return
  end

  local ok = safe_call(function()
    return build:ImportBuild(xml)
  end)
  if not ok then
    io.write("{}")
    return
  end

  build:RefreshSkillSelect()
  build:BuildModList()
  build:ProcessStatComparison()

  local stats = {
    life = build.calcsTab.mainOutput.Life or 0,
    es = build.calcsTab.mainOutput.EnergyShield or 0,
    eva = build.calcsTab.mainOutput.Evasion or 0,
    armour = build.calcsTab.mainOutput.Armour or 0,
    dps = build.calcsTab.mainOutput.TotalDPS or 0,
    ehp = build.calcsTab.mainOutput.TotalEHP or 0,
    res = {
      fire = build.calcsTab.mainOutput.FireResist or 0,
      cold = build.calcsTab.mainOutput.ColdResist or 0,
      lightning = build.calcsTab.mainOutput.LightningResist or 0,
      chaos = build.calcsTab.mainOutput.ChaosResist or 0,
    },
  }

  io.write(json.encode(stats))
end

main()
