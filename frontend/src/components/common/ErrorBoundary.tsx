import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Box, Typography, Button, Alert, AlertTitle } from '@mui/material';
import { Refresh, BugReport } from '@mui/icons-material';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  private handleRefresh = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  private handleReload = () => {
    window.location.reload();
  };

  public render() {
    if (this.state.hasError) {
      return (
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '100vh',
            p: 3,
            textAlign: 'center',
          }}
        >
          <Alert
            severity="error"
            sx={{
              maxWidth: 600,
              width: '100%',
              mb: 3,
            }}
          >
            <AlertTitle>Something went wrong</AlertTitle>
            <Typography variant="body2" sx={{ mb: 2 }}>
              We're sorry, but something unexpected happened. The error has been logged
              and our team has been notified.
            </Typography>
            
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <Box
                sx={{
                  mt: 2,
                  p: 2,
                  backgroundColor: '#f5f5f5',
                  borderRadius: 1,
                  textAlign: 'left',
                  maxHeight: 200,
                  overflow: 'auto',
                }}
              >
                <Typography variant="caption" component="pre">
                  {this.state.error.toString()}
                  {this.state.errorInfo?.componentStack}
                </Typography>
              </Box>
            )}
          </Alert>

          <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              startIcon={<Refresh />}
              onClick={this.handleRefresh}
              color="primary"
            >
              Try Again
            </Button>
            
            <Button
              variant="outlined"
              startIcon={<Refresh />}
              onClick={this.handleReload}
              color="primary"
            >
              Reload Page
            </Button>

            {process.env.NODE_ENV === 'development' && (
              <Button
                variant="text"
                startIcon={<BugReport />}
                onClick={() => console.log('Error details:', {
                  error: this.state.error,
                  errorInfo: this.state.errorInfo,
                })}
                color="secondary"
              >
                Log Details
              </Button>
            )}
          </Box>

          <Typography variant="body2" color="text.secondary" sx={{ mt: 3 }}>
            If this problem persists, please contact support with the error details.
          </Typography>
        </Box>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;