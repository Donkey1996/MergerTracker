import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Box,
  IconButton,
  Badge,
  Avatar,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  NotificationsOutlined,
  AccountCircle,
  TrendingUp,
} from '@mui/icons-material';

const Header: React.FC = () => {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  return (
    <AppBar position="static" elevation={1} sx={{ zIndex: 1201 }}>
      <Toolbar>
        {/* Logo and Title */}
        <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
          <TrendingUp sx={{ mr: 1, fontSize: '2rem' }} />
          <Typography
            variant="h5"
            component="div"
            sx={{
              fontWeight: 700,
              background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            MergerTracker
          </Typography>
        </Box>

        {/* Right side - Notifications and User Menu */}
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          {/* Notifications */}
          <IconButton
            size="large"
            color="inherit"
            aria-label="notifications"
            sx={{ mr: 2 }}
          >
            <Badge badgeContent={3} color="secondary">
              <NotificationsOutlined />
            </Badge>
          </IconButton>

          {/* User Menu */}
          <IconButton
            size="large"
            aria-label="account of current user"
            aria-controls="menu-appbar"
            aria-haspopup="true"
            onClick={handleMenu}
            color="inherit"
          >
            <Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32 }}>
              U
            </Avatar>
          </IconButton>
          <Menu
            id="menu-appbar"
            anchorEl={anchorEl}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            keepMounted
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            open={Boolean(anchorEl)}
            onClose={handleClose}
          >
            <MenuItem onClick={handleClose}>Profile</MenuItem>
            <MenuItem onClick={handleClose}>Settings</MenuItem>
            <MenuItem onClick={handleClose}>Logout</MenuItem>
          </Menu>
        </Box>
      </Toolbar>
    </AppBar>
  );
};

export default Header;