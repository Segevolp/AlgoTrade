import React from "react";
import {
  AppBar,
  Toolbar,
  Tabs,
  Tab,
  Typography,
  Box,
  Switch,
} from "@mui/material";
import { useNavigate, useLocation } from "react-router-dom";
import { useThemeMode } from "../../contexts/ThemeContext";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";

const tabs = [
  { label: "Home", path: "/" },
  { label: "LSTM", path: "/lstm" },
  { label: "Algo2", path: "/algo2" },
  { label: "Algo3", path: "/algo3" },
  { label: "Algo4", path: "/algo4" },
];

function Navbar() {
  const { toggleTheme, mode } = useThemeMode();
  const navigate = useNavigate();
  const location = useLocation();
  const currentTab = tabs.findIndex((tab) => tab.path === location.pathname);

  const handleTabChange = (e, newValue) => {
    navigate(tabs[newValue].path);
  };

  return (
    <AppBar position="static" color="primary">
      <Toolbar sx={{ justifyContent: "space-between" }}>
        <Box display="flex" alignItems="center">
          <Typography variant="h6" sx={{ mr: 4 }}>
            AlgoForecast
          </Typography>
          <Tabs
            value={currentTab}
            onChange={handleTabChange}
            textColor="inherit"
            indicatorColor="secondary"
          >
            {tabs.map((tab, idx) => (
              <Tab key={idx} label={tab.label} />
            ))}
          </Tabs>
        </Box>

        {/* Theme Toggle */}
        <Box display="flex" alignItems="center">
          <Switch checked={mode === "dark"} onChange={toggleTheme} />
          {mode === "dark" ? <DarkModeIcon /> : <LightModeIcon />}
        </Box>
      </Toolbar>
    </AppBar>
  );
}

export default Navbar;
