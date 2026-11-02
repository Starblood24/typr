local wezterm = require 'wezterm'
local callbacks, toggles, fullscreen = {}, 0, false
local gui = {
  get_dimensions = function() return { is_full_screen = fullscreen } end,
  toggle_fullscreen = function() toggles = toggles + 1; fullscreen = true end,
}
local mock = setmetatable({
  on = function(name, callback) callbacks[name] = callback end,
  mux = {
    get_active_workspace = function() return 'typr-test' end,
    all_windows = function() return {
      { get_workspace = function() return 'typr-test' end, gui_window = function() return gui end },
      { get_workspace = function() return 'other' end, gui_window = function() error('Unrelated workspace touched') end },
    } end,
  },
}, { __index = wezterm })
package.loaded.wezterm = mock
local config = dofile(wezterm.config_dir .. '/../src/typr/assets/wezterm-fullscreen.lua')
package.loaded.wezterm = wezterm
assert(type(config) == 'table', 'User configuration was not returned')
callbacks['gui-attached']()
callbacks['gui-attached']()
assert(fullscreen and toggles == 1, 'Fullscreen must be enabled once, not toggled off on reattach')
return config
