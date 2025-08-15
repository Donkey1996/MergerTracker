import React from 'react';
import { Box, Typography, Card, CardContent } from '@mui/material';

const News: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        M&A News
      </Typography>
      <Card>
        <CardContent>
          <Typography>
            News page - will display aggregated M&A news from multiple sources.
            Features will include:
            - AI-generated summaries
            - Source filtering
            - Relevance scoring
            - Date range filtering
            - Search functionality
            - Link to original articles
            - Deal association
          </Typography>
        </CardContent>
      </Card>
    </Box>
  );
};

export default News;