import React from 'react';
import { Paper, Typography, Box } from '@mui/material';
import { useScrollReveal } from '../utils/hooks/useScrollReveal';

interface ChatBubbleProps {
  speaker: string;
  dialogue: string;
}

const ChatBubble: React.FC<ChatBubbleProps> = ({ speaker, dialogue }) => {
  const { ref, visible } = useScrollReveal(0.2);

  return (
    <Box
      ref={ref}
      sx={{
        display: 'flex',
        flexDirection: speaker === 'Customer' ? 'row-reverse' : 'row',
        alignItems: 'flex-end',
        mb: 2,
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(20px)',
        transition: 'opacity 0.7s ease-out, transform 0.7s ease-out',
      }}
    >
      <Paper
        sx={{
          p: 1.5,
          bgcolor: speaker === 'Customer' ? 'primary.light' : 'grey.200',
          // Use theme's contrast text color for customer, and always dark text for agent
          color: speaker === 'Customer' ? 'primary.contrastText' : 'grey.900',
          borderRadius: 3,
          minWidth: 100,
          maxWidth: 400,
        }}
      >
        <Typography variant="body2" fontWeight={600}>{speaker}</Typography>
        <Typography variant="body1">{dialogue}</Typography>
      </Paper>
    </Box>
  );
};

export default ChatBubble;
