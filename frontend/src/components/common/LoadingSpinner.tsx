import React from 'react';
import {
  Box,
  CircularProgress,
  Typography,
  useTheme,
} from '@mui/material';
import { SxProps, Theme } from '@mui/material/styles';

interface LoadingSpinnerProps {
  size?: number;
  message?: string;
  fullScreen?: boolean;
  sx?: SxProps<Theme>;
  color?: 'primary' | 'secondary' | 'inherit';
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 40,
  message = 'Loading...',
  fullScreen = false,
  sx,
  color = 'primary',
}) => {
  const theme = useTheme();

  const containerStyle: SxProps<Theme> = {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 2,
    ...(fullScreen && {
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: theme.palette.background.default,
      zIndex: theme.zIndex.modal,
    }),
    ...sx,
  };

  return (
    <Box sx={containerStyle} role="status" aria-label={message}>
      <CircularProgress size={size} color={color} />
      {message && (
        <Typography
          variant="body2"
          color="text.secondary"
          textAlign="center"
        >
          {message}
        </Typography>
      )}
    </Box>
  );
};

// Skeleton loading component for content placeholders
export const SkeletonLoader: React.FC<{
  variant?: 'text' | 'rectangular' | 'circular';
  width?: string | number;
  height?: string | number;
  count?: number;
  sx?: SxProps<Theme>;
}> = ({
  variant = 'text',
  width = '100%',
  height = variant === 'text' ? '1.2em' : 118,
  count = 1,
  sx,
}) => {
  return (
    <Box sx={sx}>
      {Array.from({ length: count }, (_, index) => (
        <Box
          key={index}
          sx={{
            width,
            height,
            backgroundColor: 'action.hover',
            borderRadius: variant === 'circular' ? '50%' : 1,
            mb: variant === 'text' ? 0.5 : 1,
            animation: 'pulse 1.5s ease-in-out infinite',
            '@keyframes pulse': {
              '0%': {
                opacity: 1,
              },
              '50%': {
                opacity: 0.4,
              },
              '100%': {
                opacity: 1,
              },
            },
          }}
        />
      ))}
    </Box>
  );
};

// Full page loading component
export const PageLoader: React.FC<{ message?: string }> = ({
  message = 'Loading page...',
}) => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '60vh',
        gap: 3,
      }}
    >
      <CircularProgress size={60} />
      <Typography variant="h6" color="text.secondary">
        {message}
      </Typography>
    </Box>
  );
};

// Inline loading for buttons and small components
export const InlineLoader: React.FC<{
  size?: number;
  color?: 'primary' | 'secondary' | 'inherit';
}> = ({ size = 20, color = 'inherit' }) => {
  return (
    <CircularProgress
      size={size}
      color={color}
      sx={{
        display: 'inline-block',
        verticalAlign: 'middle',
      }}
    />
  );
};

export default LoadingSpinner;