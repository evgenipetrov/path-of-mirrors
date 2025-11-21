-- PoB bridge: run PoB headless with a build XML on stdin and emit JSON stats.
-- Usage: luajit pob_bridge.lua /path/to/Path\ of\ Building.exe
--
-- Minimal, non-blocking: on any failure, prints '{}' and exits 0 so callers can
-- fall back to lightweight parsing without breaking workflows.

local ffi = require("ffi")

-- tiny JSON encoder for the limited structures we emit (numbers, strings,
-- booleans, flat tables with string keys, arrays)
local function is_array(t)
  local count = 0
  for k, _ in pairs(t) do
    count = count + 1
    if type(k) ~= "number" then
      return false
    end
  end
  return count == #t
end

local function escape_str(s)
  return s:gsub("\\", "\\\\"):gsub("\"", "\\\""):gsub("\n", "\\n"):gsub("\r", "\\r")
end

local function encode(v)
  local tv = type(v)
  if tv == "nil" then return "null" end
  if tv == "boolean" or tv == "number" then return tostring(v) end
  if tv == "string" then return '"' .. escape_str(v) .. '"' end
  if tv == "table" then
    if is_array(v) then
      local parts = {}
      for i = 1, #v do parts[#parts+1] = encode(v[i]) end
      return "[" .. table.concat(parts, ",") .. "]"
    else
      local parts = {}
      for k, val in pairs(v) do
        parts[#parts+1] = '"' .. escape_str(tostring(k)) .. '":' .. encode(val)
      end
      return "{" .. table.concat(parts, ",") .. "}"
    end
  end
  return '""'
end

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
  return table.concat(chunks, "\n")
end

local function safe_call(fn, ...)
  local ok, res = pcall(fn, ...)
  if not ok then
    return nil
  end
  return res
end

local function change_directory(target)
  local is_windows = package.config:sub(1, 1) == "\\"
  if is_windows then
    ffi.cdef[[ int _chdir(const char *path); ]]
    ffi.C._chdir(target)
  else
    ffi.cdef[[ int chdir(const char *path); ]]
    ffi.C.chdir(target)
  end
end

local function main()
  local xml = read_stdin()
  if xml == "" then
    io.write("{}")
    return
  end

  local exe_dir = exe_path:match("^(.*)[/\\][^/\\]+$") or "."
  local cwd = os.getenv("PWD") or "."
  local abs_exe_dir = exe_dir:sub(1,1) == "/" and exe_dir or (cwd .. "/" .. exe_dir)
  change_directory(abs_exe_dir)

  -- shim utf8 module with a pure-Lua version when running outside Windows
  package.preload["lua-utf8"] = function()
    return dofile(abs_exe_dir .. "/lua-utf8.lua")
  end

  package.path = table.concat({
    abs_exe_dir .. "/?.lua",
    abs_exe_dir .. "/lua/?.lua",
    abs_exe_dir .. "/lua/?/init.lua",
    package.path,
  }, ";")

  -- Load PoB headless bootstrap
  local is_windows = package.config:sub(1, 1) == "\\"
  local null_device = is_windows and "NUL" or "/dev/null"

  local old_stdout, old_stderr = io.stdout, io.stderr
  local tmp_out = io.open(null_device, "w")
  local tmp_err = io.open(null_device, "w")
  io.stdout = tmp_out
  io.stderr = tmp_err

  local ok_headless, headless_err = pcall(function()
    dofile(abs_exe_dir .. "/HeadlessWrapper.lua")
  end)

  io.stdout = old_stdout
  io.stderr = old_stderr
  tmp_out:close()
  tmp_err:close()

  if not ok_headless then
    io.stderr:write("[pob_bridge] failed loading HeadlessWrapper: " .. tostring(headless_err) .. "\n")
    io.write("{}")
    return
  end

  if type(newBuild) == "function" then
    newBuild()
  end

  local load_build = loadBuildFromXML or LoadBuildFromXML or loadBuildFromXMLFile
  if not load_build then
    io.write("{}")
    return
  end

  local ok_import, import_err = pcall(function()
    local old_out, old_err = io.stdout, io.stderr
    local tmp = io.open(null_device, "w")
    io.stdout = tmp
    io.stderr = tmp
    local result = load_build(xml, "path-of-mirrors")
    io.stdout = old_out
    io.stderr = old_err
    tmp:close()
    return result
  end)
  if not ok_import then
    io.stderr:write("[pob_bridge] loadBuildFromXML failed: " .. tostring(import_err) .. "\n")
    io.write("{}")
    return
  end

  local out = build and build.calcsTab and build.calcsTab.mainOutput or {}

  local stats = {
    life = out.Life or 0,
    es = out.EnergyShield or 0,
    eva = out.Evasion or 0,
    armour = out.Armour or 0,
    dps = out.TotalDPS or out.CombinedDPS or out.WithPoisonDPS or 0,
    ehp = out.TotalEHP or 0,
    res = {
      fire = out.FireResist or 0,
      cold = out.ColdResist or 0,
      lightning = out.LightningResist or 0,
      chaos = out.ChaosResist or 0,
    },
  }

  io.write(encode(stats))
end

main()
