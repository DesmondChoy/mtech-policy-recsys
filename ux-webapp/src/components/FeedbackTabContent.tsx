import React, { useState } from 'react';
import { Box, Typography, TextField, Button, Stack, Snackbar, Alert } from '@mui/material';

const predefinedFeedback = [
  "My requirement has changed since the last call. I would like to update please.",
  "This recommendation is helpful and matches what I need.",
  "The recommended policy doesn't seem to cover one of my key requirements."
];

const FeedbackTabContent: React.FC = () => {
  const [feedbackText, setFeedbackText] = useState('');
  const [snackbarOpen, setSnackbarOpen] = useState(false);

  const handlePredefinedClick = (text: string) => {
    setFeedbackText((prevText) => (prevText ? `${prevText}\n${text}` : text));
  };

  const handleSendClick = () => {
    // PoC: Just show the snackbar, don't actually send anything
    setSnackbarOpen(true);
    // Optionally clear the text field after "sending"
    // setFeedbackText('');
  };

  // Prefix unused 'event' parameter with underscore to satisfy TS6133
  const handleSnackbarClose = (_event?: React.SyntheticEvent | Event, reason?: string) => {
    if (reason === 'clickaway') {
      return;
    }
    setSnackbarOpen(false);
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Provide Feedback
      </Typography>
      {/* Split into two Typography components for separate lines */}
      <Typography variant="body1" color="text.secondary">
        We would love your feedback on what you love about the app and where you could do better.
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}> {/* Add margin bottom for spacing before buttons */}
        Drop us a message below and we'll get back to you soon!
      </Typography>

      {/* Remove spacing prop, control spacing via margin on Button */}
      <Stack direction="row" mb={2} flexWrap="wrap" justifyContent="flex-start">
        {predefinedFeedback.map((text, index) => (
          <Button
            key={index}
            variant="contained"
            size="small"
            onClick={() => handlePredefinedClick(text)}
            sx={(theme) => ({ // Use theme callback for palette access
              mb: 1, // Margin bottom for wrapped items
              mr: 1, // Margin right for spacing between items on the same line
              textTransform: 'none', // Prevent uppercase
              borderRadius: '16px', // Make it rounded like a chip/bubble
              bgcolor: theme.palette.primary.light, // Use light primary blue
              color: theme.palette.primary.contrastText, // Ensure contrast text
              '&:hover': {
                bgcolor: theme.palette.primary.main, // Use main primary blue on hover
              }
            })}
          >
            {text}
          </Button>
        ))}
      </Stack>

      <TextField
        label="Your Feedback"
        multiline
        rows={6}
        fullWidth
        value={feedbackText}
        onChange={(e) => setFeedbackText(e.target.value)}
        variant="outlined"
        sx={{ mb: 2 }}
      />

      <Button
        variant="contained"
        onClick={handleSendClick}
        disabled={!feedbackText.trim()} // Disable if text area is empty
      >
        Send Feedback
      </Button>

      <Snackbar
        open={snackbarOpen}
        autoHideDuration={4000} // Hide after 4 seconds
        onClose={handleSnackbarClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert onClose={handleSnackbarClose} severity="success" sx={{ width: '100%' }}>
          Thank you for your feedback! A customer representative will be in touch shortly.
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default FeedbackTabContent;
