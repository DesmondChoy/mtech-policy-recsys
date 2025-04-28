import React, { useEffect, useState } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material'; // Added Typography

// Helper function to safely get nested data
const getDataAtPath = (obj: any, path: string): any => {
  if (!path) return obj;
  const keys = path.split('.');
  let current = obj;
  for (const key of keys) {
    if (current === null || typeof current !== 'object' || !(key in current)) {
      return undefined; // Path doesn't exist
    }
    current = current[key];
  }
  return current;
};


export const JsonPrettyViewer: React.FC<{ filePath: string; dataPath?: string }> = ({ filePath, dataPath }) => {
  const [content, setContent] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null); // Use separate error state

  useEffect(() => {
    setLoading(true);
    setError(null); // Reset error on new fetch
    setContent(null); // Reset content
    const controller = new AbortController();

    fetch(filePath, { signal: controller.signal })
      .then(res => {
        if (!res.ok) throw new Error(`File not found at ${filePath}`);
        return res.json();
      })
      .then(json => {
        const dataToDisplay = dataPath ? getDataAtPath(json, dataPath) : json;
        if (dataPath && dataToDisplay === undefined) {
          throw new Error(`Data path "${dataPath}" not found in JSON file.`);
        }
        setContent(dataToDisplay);
      })
      .catch(err => {
        if (err.name === 'AbortError') return;
        console.error(`Error loading/processing JSON from ${filePath}:`, err);
        setError(err.message || 'Failed to load or process JSON file.');
      })
      .finally(() => setLoading(false));

      return () => controller.abort();
  }, [filePath, dataPath]); // Add dataPath to dependency array

  if (loading) return <Box sx={{ textAlign: 'center', py: 4 }}><CircularProgress /></Box>;
  if (error) return <Typography color="error" sx={{ py: 2 }}>{error}</Typography>;
  if (content === null) return <Typography sx={{ py: 2 }}>No content to display.</Typography>; // Handle case where content is validly null/empty after extraction

  return (
    <Box sx={{ 
      fontFamily: 'monospace', 
      fontSize: '0.9rem', 
      bgcolor: 'background.paper', 
      color: 'text.primary',
      px: 2, 
      py: 2, 
      borderRadius: 2, 
      overflowX: 'auto', 
      whiteSpace: 'pre' 
    }}>
      {JSON.stringify(content, null, 2)}
    </Box>
  );
};
