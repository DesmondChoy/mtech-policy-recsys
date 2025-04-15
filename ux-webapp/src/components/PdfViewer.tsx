import React from 'react';
import { Box, Typography } from '@mui/material';

export const PdfViewer: React.FC<{ filePath: string }> = ({ filePath }) => {
  return (
    <Box sx={{ border: '1px solid #e0e0e0', borderRadius: 2, overflow: 'hidden', bgcolor: '#fff' }}>
      <object data={filePath} type="application/pdf" width="100%" height="500px">
        <Typography variant="body2" color="text.secondary" align="center" sx={{ p: 2 }}>
          PDF preview not available. <a href={filePath} target="_blank" rel="noopener noreferrer">Download PDF</a>
        </Typography>
      </object>
    </Box>
  );
};
