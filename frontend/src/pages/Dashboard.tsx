import React from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Avatar,
  LinearProgress,
} from '@mui/material';
import {
  TrendingUp,
  Business,
  Article,
  AttachMoney,
  ArrowUpward,
  ArrowDownward,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

// Mock data - replace with real API calls
const mockStats = {
  totalDeals: 1247,
  totalValue: 456.7,
  activeDeals: 89,
  completedDeals: 1158,
  weeklyGrowth: 12.5,
  monthlyGrowth: -3.2,
};

const mockRecentDeals = [
  {
    id: '1',
    target: 'TechCorp Inc.',
    acquirer: 'MegaTech Solutions',
    value: 12.4,
    status: 'announced',
    date: '2024-01-15',
    type: 'acquisition',
  },
  {
    id: '2',
    target: 'DataSoft LLC',
    acquirer: 'Cloud Innovations',
    value: 8.9,
    status: 'pending',
    date: '2024-01-14',
    type: 'merger',
  },
  {
    id: '3',
    target: 'GreenEnergy Co.',
    acquirer: 'Renewable Holdings',
    value: 25.6,
    status: 'completed',
    date: '2024-01-13',
    type: 'acquisition',
  },
];

const mockRecentNews = [
  {
    id: '1',
    headline: 'Major Tech Acquisition Expected to Close Q2',
    source: 'Financial Times',
    time: '2 hours ago',
    relevance: 0.95,
  },
  {
    id: '2',
    headline: 'Healthcare Merger Creates Industry Giant',
    source: 'Wall Street Journal',
    time: '4 hours ago',
    relevance: 0.87,
  },
  {
    id: '3',
    headline: 'Energy Sector Consolidation Continues with Latest Deal',
    source: 'Reuters',
    time: '6 hours ago',
    relevance: 0.92,
  },
];

const Dashboard: React.FC = () => {
  const navigate = useNavigate();

  const formatCurrency = (value: number) => {
    return `$${value.toFixed(1)}B`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString();
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'announced':
        return 'info';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      {/* Page Header */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Dashboard
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Overview of M&A market activity and recent developments
        </Typography>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Avatar sx={{ bgcolor: 'primary.main', mr: 2 }}>
                  <Business />
                </Avatar>
                <Box>
                  <Typography variant="h4" component="div">
                    {mockStats.totalDeals.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Deals
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Avatar sx={{ bgcolor: 'success.main', mr: 2 }}>
                  <AttachMoney />
                </Avatar>
                <Box>
                  <Typography variant="h4" component="div">
                    {formatCurrency(mockStats.totalValue)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Value
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Avatar sx={{ bgcolor: 'warning.main', mr: 2 }}>
                  <TrendingUp />
                </Avatar>
                <Box>
                  <Typography variant="h4" component="div">
                    {mockStats.activeDeals}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Active Deals
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                <Avatar sx={{ bgcolor: 'info.main', mr: 2 }}>
                  <Article />
                </Avatar>
                <Box>
                  <Typography variant="h4" component="div">
                    {mockStats.completedDeals.toLocaleString()}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Completed
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Growth Indicators */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Weekly Growth
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ArrowUpward color="success" sx={{ mr: 1 }} />
                <Typography variant="h5" color="success.main">
                  +{mockStats.weeklyGrowth}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={mockStats.weeklyGrowth}
                color="success"
                sx={{ height: 8, borderRadius: 4 }}
              />
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Monthly Growth
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <ArrowDownward color="error" sx={{ mr: 1 }} />
                <Typography variant="h5" color="error.main">
                  {mockStats.monthlyGrowth}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={Math.abs(mockStats.monthlyGrowth)}
                color="error"
                sx={{ height: 8, borderRadius: 4 }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" component="div">
                  Recent Deals
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => navigate('/deals')}
                >
                  View All
                </Button>
              </Box>
              <TableContainer>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Target</TableCell>
                      <TableCell>Acquirer</TableCell>
                      <TableCell>Value</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Date</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {mockRecentDeals.map((deal) => (
                      <TableRow
                        key={deal.id}
                        sx={{ '&:hover': { backgroundColor: 'action.hover' } }}
                        onClick={() => navigate(`/deals/${deal.id}`)}
                        style={{ cursor: 'pointer' }}
                      >
                        <TableCell>{deal.target}</TableCell>
                        <TableCell>{deal.acquirer}</TableCell>
                        <TableCell>{formatCurrency(deal.value)}</TableCell>
                        <TableCell>
                          <Chip
                            label={deal.status.toUpperCase()}
                            size="small"
                            color={getStatusColor(deal.status) as any}
                          />
                        </TableCell>
                        <TableCell>{formatDate(deal.date)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} lg={4}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" component="div">
                  Latest News
                </Typography>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => navigate('/news')}
                >
                  View All
                </Button>
              </Box>
              <Box>
                {mockRecentNews.map((article) => (
                  <Box
                    key={article.id}
                    sx={{
                      p: 2,
                      mb: 2,
                      borderRadius: 1,
                      backgroundColor: 'background.default',
                      cursor: 'pointer',
                      '&:hover': {
                        backgroundColor: 'action.hover',
                      },
                    }}
                    onClick={() => navigate('/news')}
                  >
                    <Typography variant="subtitle2" gutterBottom>
                      {article.headline}
                    </Typography>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="caption" color="text.secondary">
                        {article.source} • {article.time}
                      </Typography>
                      <Chip
                        label={`${Math.round(article.relevance * 100)}%`}
                        size="small"
                        variant="outlined"
                        color="primary"
                      />
                    </Box>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard;