import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

const Deals: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        M&A Deals
      </Typography>
      <Card>
        <CardContent>
          <Typography>
            Deals page - will display filterable list of M&A deals with detailed information.
            Features will include:
            - Advanced filtering by status, type, value, date ranges
            - Search functionality
            - Sortable columns
            - Pagination
            - Export capabilities
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Deals;