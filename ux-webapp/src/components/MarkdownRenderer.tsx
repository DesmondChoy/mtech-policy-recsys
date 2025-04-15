import React, { useEffect, useState } from 'react';
import { Box, CircularProgress } from '@mui/material';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export const MarkdownRenderer: React.FC<{ filePath: string; animate?: boolean }> = ({ filePath, animate }) => {
  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setContent('');
    setError(null);
    const controller = new AbortController();
    fetch(filePath, { signal: controller.signal })
      .then(res => {
        if (!res.ok) throw new Error('File not found');
        return res.text();
      })
      .then(text => setContent(text))
      .catch(err => {
        if (err.name === 'AbortError') return;
        setError('Failed to load markdown file.');
      })
      .finally(() => setLoading(false));
    return () => controller.abort();
  }, [filePath]);

  // Optionally animate streaming text (typewriter effect)
  const [displayed, setDisplayed] = useState('');
  useEffect(() => {
    if (!animate || !content) {
      setDisplayed(content);
      return;
    }
    setDisplayed('');
    let i = 0;
    const interval = setInterval(() => {
      setDisplayed(content.slice(0, i));
      i++;
      if (i > content.length) clearInterval(interval);
    }, 8);
    return () => clearInterval(interval);
  }, [content, animate]);

  if (loading) return <Box sx={{ textAlign: 'center', py: 4 }}><CircularProgress /></Box>;
  if (error) return <Box sx={{ color: 'error.main', py: 2 }}>{error}</Box>;
  return (
    <Box sx={{ fontSize: '1rem', lineHeight: 1.7, px: 1 }}>
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{displayed}</ReactMarkdown>
    </Box>
  );
};
