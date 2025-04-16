import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Typography, CircularProgress } from '@mui/material';

const TransitionPage: React.FC = () => {
  const { uuid } = useParams<{ uuid: string }>();
  const navigate = useNavigate();

  useEffect(() => {
    // Placeholder for animation, then navigate to report
    const timeout = setTimeout(() => {
      navigate(`/report/${uuid}`);
    }, 1800);
    return () => clearTimeout(timeout);
  }, [navigate, uuid]);

  return (
    <Box sx={{ minHeight: '60vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
      <CircularProgress sx={{ mb: 3 }} />
      <Typography variant="h6">Loading your personalized experience...</Typography>
    </Box>
  );
};

export default TransitionPage;
