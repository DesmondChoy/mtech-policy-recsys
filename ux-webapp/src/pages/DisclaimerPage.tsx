import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Typography, Button, Paper } from '@mui/material'; // Added Paper for visual grouping

const DisclaimerPage: React.FC = () => {
  const { uuid } = useParams<{ uuid: string }>();
  const navigate = useNavigate();

  const handleAccept = () => {
    if (uuid) {
      navigate(`/report/${uuid}`);
    } else {
      // Handle case where uuid might be missing, perhaps navigate home
      navigate('/');
    }
  };

  const handleLogout = () => {
    navigate('/');
  };

  return (
    <Box
      sx={{
        minHeight: '80vh', // Ensure it takes significant height
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        px: 2, // Add some horizontal padding
      }}
    >
      <Paper elevation={3} sx={{ p: 4, maxWidth: 500, width: '100%', textAlign: 'center' }}>
        <Typography variant="h6" gutterBottom sx={{ mb: 2, fontWeight: 'bold' }}>
          Disclaimer
        </Typography>
        <Typography variant="body1" sx={{ mb: 3 }}>
          The following reports are AI-generated and can contain mistakes.
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2, mt: 2 }}>
          <Button variant="contained" color="primary" onClick={handleAccept}>
            I understand
          </Button>
          <Button variant="outlined" color="secondary" onClick={handleLogout}>
            Log out
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default DisclaimerPage;
