import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Box,
  Divider,
} from '@mui/material';
import {
  DashboardOutlined,
  BusinessOutlined,
  ArticleOutlined,
  TrendingUpOutlined,
  HandshakeOutlined,
} from '@mui/icons-material';

const DRAWER_WIDTH = 240;

interface NavigationItem {
  text: string;
  path: string;
  icon: React.ReactElement;
}

const navigationItems: NavigationItem[] = [
  {
    text: 'Dashboard',
    path: '/',
    icon: <DashboardOutlined />,
  },
  {
    text: 'Deals',
    path: '/deals',
    icon: <HandshakeOutlined />,
  },
  {
    text: 'News',
    path: '/news',
    icon: <ArticleOutlined />,
  },
  {
    text: 'Companies',
    path: '/companies',
    icon: <BusinessOutlined />,
  },
  {
    text: 'Analytics',
    path: '/analytics',
    icon: <TrendingUpOutlined />,
  },
];

const Navigation: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const handleNavigate = (path: string) => {
    navigate(path);
  };

  return (
    <Drawer
      variant="permanent"
      sx={{
        width: DRAWER_WIDTH,
        flexShrink: 0,
        '& .MuiDrawer-paper': {
          width: DRAWER_WIDTH,
          boxSizing: 'border-box',
          position: 'relative',
          borderRight: '1px solid rgba(0, 0, 0, 0.12)',
          backgroundColor: 'background.paper',
        },
      }}
    >
      <Box sx={{ overflow: 'auto', pt: 2 }}>
        <List>
          {navigationItems.map((item) => (
            <ListItem key={item.text} disablePadding sx={{ mb: 0.5 }}>
              <ListItemButton
                selected={location.pathname === item.path}
                onClick={() => handleNavigate(item.path)}
                sx={{
                  mx: 1,
                  borderRadius: 1,
                  '&.Mui-selected': {
                    backgroundColor: 'primary.main',
                    color: 'primary.contrastText',
                    '& .MuiListItemIcon-root': {
                      color: 'primary.contrastText',
                    },
                    '&:hover': {
                      backgroundColor: 'primary.dark',
                    },
                  },
                  '&:hover': {
                    backgroundColor: 'action.hover',
                  },
                }}
              >
                <ListItemIcon
                  sx={{
                    minWidth: 40,
                    color: location.pathname === item.path ? 'inherit' : 'text.secondary',
                  }}
                >
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.text}
                  primaryTypographyProps={{
                    fontSize: '0.875rem',
                    fontWeight: location.pathname === item.path ? 600 : 400,
                  }}
                />
              </ListItemButton>
            </ListItem>
          ))}
        </List>
        
        <Divider sx={{ my: 2, mx: 2 }} />
        
        {/* Quick Stats */}
        <Box sx={{ px: 2, py: 1 }}>
          <Box
            sx={{
              backgroundColor: 'background.default',
              borderRadius: 1,
              p: 2,
              textAlign: 'center',
            }}
          >
            <Box sx={{ fontSize: '1.5rem', fontWeight: 700, color: 'primary.main' }}>
              42
            </Box>
            <Box sx={{ fontSize: '0.75rem', color: 'text.secondary', mt: 0.5 }}>
              New Deals This Week
            </Box>
          </Box>
        </Box>
        
        <Box sx={{ px: 2, py: 1 }}>
          <Box
            sx={{
              backgroundColor: 'background.default',
              borderRadius: 1,
              p: 2,
              textAlign: 'center',
            }}
          >
            <Box sx={{ fontSize: '1.5rem', fontWeight: 700, color: 'secondary.main' }}>
              $12.4B
            </Box>
            <Box sx={{ fontSize: '0.75rem', color: 'text.secondary', mt: 0.5 }}>
              Total Deal Value
            </Box>
          </Box>
        </Box>
      </Box>
    </Drawer>
  );
};

export default Navigation;