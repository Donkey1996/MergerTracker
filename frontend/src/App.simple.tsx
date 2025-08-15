import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Box, Typography } from '@mui/material';

// Simple components (create dummy components if originals have import issues)
// import Header from './components/common/Header';
// import Navigation from './components/common/Navigation';
import Dashboard from './pages/Dashboard';

// Simple placeholder components for header and navigation
const Header = () => (
  <Box sx={{ p: 2, bgcolor: 'primary.main', color: 'white' }}>
    <Typography variant="h5">MergerTracker</Typography>
  </Box>
);

const Navigation = () => (
  <Box sx={{ width: 240, bgcolor: 'grey.100', p: 2 }}>
    <Typography variant="h6" gutterBottom>Navigation</Typography>
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
      <Typography variant="body2">Dashboard</Typography>
      <Typography variant="body2">Deals</Typography>
      <Typography variant="body2">Companies</Typography>
      <Typography variant="body2">News</Typography>
      <Typography variant="body2">Analytics</Typography>
    </Box>
  </Box>
);

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

// Simple placeholder components
const SimpleDeals = () => <Box p={3}>Deals page coming soon...</Box>;
const SimpleNews = () => <Box p={3}>News page coming soon...</Box>;
const SimpleCompanies = () => <Box p={3}>Companies page coming soon...</Box>;
const SimpleAnalytics = () => <Box p={3}>Analytics page coming soon...</Box>;

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
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
                <Route path="/deals" element={<SimpleDeals />} />
                <Route path="/news" element={<SimpleNews />} />
                <Route path="/companies" element={<SimpleCompanies />} />
                <Route path="/analytics" element={<SimpleAnalytics />} />
              </Routes>
            </Box>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
}

export default App;