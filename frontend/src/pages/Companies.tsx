import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

const Companies: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Companies
      </Typography>
      <Card>
        <CardContent>
          <Typography>
            Companies page - will display company profiles and deal history.
            Features will include:
            - Company search and filtering
            - Industry categorization
            - Deal participation history
            - Company details and metrics
            - Market cap and financial info
            - Links to related deals
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Companies;