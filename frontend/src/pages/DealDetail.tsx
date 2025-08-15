import React from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, Card, CardContent } from '@mui/material';

const DealDetail: React.FC = () => {
  const { dealId } = useParams<{ dealId: string }>();

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Deal Details
      </Typography>
      <Card>
        <CardContent>
          <Typography>
            Deal detail page for deal ID: {dealId}
            
            This page will show:
            - Complete deal information
            - Company profiles (target/acquirer)
            - Financial metrics and multiples
            - Timeline and status updates
            - Related news articles
            - Advisor information
            - Regulatory status
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default DealDetail;