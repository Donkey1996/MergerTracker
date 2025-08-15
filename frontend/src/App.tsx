import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box } from '@mui/material';

import Header from './components/common/Header';
import Navigation from './components/common/Navigation';
import Dashboard from './pages/Dashboard';
import Deals from './pages/Deals';
import DealDetail from './pages/DealDetail';
import News from './pages/News';
import Companies from './pages/Companies';
import CompanyDetail from './pages/CompanyDetail';
import Analytics from './pages/Analytics';
import ErrorBoundary from './components/common/ErrorBoundary';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Create theme
const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#1976d2',
      light: '#42a5f5',
      dark: '#1565c0',
    },
    secondary: {
      main: '#dc004e',
      light: '#ff5983',
      dark: '#9a0036',
    },
    background: {
      default: '#f5f5f5',
      paper: '#ffffff',
    },
    text: {
      primary: '#333333',
      secondary: '#666666',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 600,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 600,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 500,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 500,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 500,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: '8px',
        },
      },
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <ErrorBoundary>
          <Router>
            <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
              <Header />
              <Box sx={{ display: 'flex', flex: 1 }}>
                <Navigation />
                <Box 
                  component="main" 
                  sx={{ 
                    flex: 1, 
                    p: 3, 
                    backgroundColor: 'background.default',
                    minHeight: '100vh'
                  }}
                >
                  <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/deals" element={<Deals />} />
                    <Route path="/deals/:dealId" element={<DealDetail />} />
                    <Route path="/news" element={<News />} />
                    <Route path="/companies" element={<Companies />} />
                    <Route path="/companies/:companyId" element={<CompanyDetail />} />
                    <Route path="/analytics" element={<Analytics />} />
                  </Routes>
                </Box>
              </Box>
            </Box>
          </Router>
        </ErrorBoundary>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;