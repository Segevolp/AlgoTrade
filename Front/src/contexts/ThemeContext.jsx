import React, { createContext, useMemo, useState, useContext } from 'react';
import { createTheme, ThemeProvider as MuiThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

const ThemeContext = createContext();

export const useThemeMode = () => useContext(ThemeContext);

export function ThemeProvider({ children }) {
  const [mode, setMode] = useState('light');

  const toggleTheme = () => setMode(prev => (prev === 'light' ? 'dark' : 'light'));

  const theme = useMemo(() =>
    createTheme({
      palette: {
        mode,
        primary: {
          main: mode === 'light' ? '#1976d2' : '#90caf9',
        },
        background: {
          default: mode === 'light' ? '#fafafa' : '#121212',
        },
      },
    }), [mode]);

  return (
    <ThemeContext.Provider value={{ toggleTheme, mode }}>
      <MuiThemeProvider theme={theme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
}
