local wezterm = require 'wezterm'
local config = wezterm.config_builder()
local function path_key(path)
  path = path:gsub('\\', '/')
  return wezterm.target_triple:find('windows') and path:lower() or path
end
local own_path = path_key(wezterm.config_file)

-- Reuse the user's configuration without changing it.
for _, path in ipairs {
  os.getenv('TYPR_WEZTERM_CONFIG') or '',
  os.getenv('WEZTERM_CONFIG_FILE') or '',
  (os.getenv('XDG_CONFIG_HOME') or (wezterm.home_dir .. '/.config')) .. '/wezterm/wezterm.lua',
  wezterm.home_dir .. '/.wezterm.lua',
} do
  if path ~= '' and path_key(path) ~= own_path then
    local file = io.open(path, 'r')
    if file then
      file:close()
      config = dofile(path)
      break
    end
  end
end

wezterm.on('gui-attached', function()
  local workspace = wezterm.mux.get_active_workspace()
  for _, window in ipairs(wezterm.mux.all_windows()) do
    if window:get_workspace() == workspace then
      local gui = window:gui_window()
      if gui and not gui:get_dimensions().is_full_screen then
        gui:toggle_fullscreen()
      end
    end
  end
end)

return config
