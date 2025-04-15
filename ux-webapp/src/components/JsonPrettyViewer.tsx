import React, { useEffect, useState } from 'react';
import { Box, CircularProgress } from '@mui/material';

export const JsonPrettyViewer: React.FC<{ filePath: string }> = ({ filePath }) => {
  const [content, setContent] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    setLoading(true);
    fetch(filePath)
      .then(res => res.ok ? res.json() : Promise.reject('File not found'))
      .then(json => setContent(json))
      .catch(() => setContent({ error: 'Failed to load JSON file.' }))
      .finally(() => setLoading(false));
  }, [filePath]);

  if (loading) return <Box sx={{ textAlign: 'center', py: 4 }}><CircularProgress /></Box>;
  return (
    <Box sx={{ fontFamily: 'monospace', fontSize: '1rem', bgcolor: '#f7f7fa', px: 2, py: 2, borderRadius: 2, overflowX: 'auto' }}>
      <pre>{JSON.stringify(content, null, 2)}</pre>
    </Box>
  );
};
