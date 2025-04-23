import React, { useState } from 'react';
import { Box, Typography, IconButton } from '@mui/material';
import ThumbUpAltIcon from '@mui/icons-material/ThumbUpAlt';
import ThumbDownAltIcon from '@mui/icons-material/ThumbDownAlt';
import { styled } from '@mui/material/styles';

const StyledIconButton = styled(IconButton, {
  shouldForwardProp: (prop) => prop !== 'selected' && prop !== 'colorVariant',
})<{ selected?: boolean; colorVariant?: 'success' | 'error' }>(({ theme, selected, colorVariant }) => ({
  transition: theme.transitions.create(['color', 'transform'], {
    duration: theme.transitions.duration.short,
  }),
  color: selected && colorVariant ? theme.palette[colorVariant].main : theme.palette.action.active,
  transform: selected ? 'scale(1.1)' : 'scale(1)',
  '&:hover': {
    color: colorVariant ? theme.palette[colorVariant].dark : theme.palette.action.hover,
    backgroundColor: 'transparent', // Prevent default hover background
  },
}));

const FeedbackButtons: React.FC = () => {
  const [selection, setSelection] = useState<'up' | 'down' | null>(null);

  const handleSelect = (newSelection: 'up' | 'down') => {
    setSelection((prevSelection) => (prevSelection === newSelection ? null : newSelection));
    // In a real application, you would likely send this feedback to a backend here.
  };

  return (
    <Box display="flex" alignItems="center" justifyContent="center" mt={2} mb={1} gap={1}> {/* Changed justifyContent to center */}
      <Typography variant="body2" color="text.secondary">
        Did you find this useful?
      </Typography>
      <StyledIconButton
        aria-label="Thumbs Up"
        onClick={() => handleSelect('up')}
        selected={selection === 'up'}
        colorVariant="success"
        size="small"
      >
        <ThumbUpAltIcon fontSize="small" />
      </StyledIconButton>
      <StyledIconButton
        aria-label="Thumbs Down"
        onClick={() => handleSelect('down')}
        selected={selection === 'down'}
        colorVariant="error"
        size="small"
      >
        <ThumbDownAltIcon fontSize="small" />
      </StyledIconButton>
    </Box>
  );
};

export default FeedbackButtons;
