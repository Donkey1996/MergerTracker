import React from 'react';
import { useParams } from 'react-router-dom';
import { Box, Typography, Card, CardContent } from '@mui/material';

const CompanyDetail: React.FC = () => {
  const { companyId } = useParams<{ companyId: string }>();

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Company Profile
      </Typography>
      <Card>
        <CardContent>
          <Typography>
            Company detail page for company ID: {companyId}
            
            This page will show:
            - Complete company information
            - Deal history (as target and acquirer)
            - Industry classification
            - Financial metrics
            - Recent news mentions
            - Related companies
            - Market analysis
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default CompanyDetail;