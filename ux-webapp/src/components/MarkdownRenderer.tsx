import React, { useEffect, useState } from 'react'; // Removed useRef, useCallback
import { Box, CircularProgress } from '@mui/material';
import ReactMarkdown from 'react-markdown';
// Removed incorrect PluggableList import
import remarkGfm from 'remark-gfm';
import rehypeSlug from 'rehype-slug'; // Import rehype-slug
import { remarkExtractHeadings, type HeadingData } from './remark-extract-headings'; // Updated path after moving file

// Define animation modes
type AnimationMode = 'character' | 'paragraph' | 'none';

interface MarkdownRendererProps {
  filePath: string;
  animationMode?: AnimationMode;
  onHeadingsExtracted?: (headings: HeadingData[]) => void; // Add callback prop
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  filePath,
  animationMode = 'none',
  onHeadingsExtracted,
}) => {
  const [content, setContent] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  // Removed headingsRef, handleHeadingsExtractionDuringRender, and the useEffect hook for calling onHeadingsExtracted

  useEffect(() => {
    setLoading(true);
    setContent('');
    setError(null);
    // headingsRef.current = []; // Removed this line as headingsRef is no longer used here
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

  // Animation effect based on mode
  const [displayed, setDisplayed] = useState('');
  useEffect(() => {
    // No animation or no content yet
    if (animationMode === 'none' || !content) {
      setDisplayed(content);
      return () => {}; // No interval to clear
    }

    setDisplayed(''); // Reset display for animation start
    let intervalId: number | undefined; // Changed type from NodeJS.Timeout to number

    if (animationMode === 'character') {
      let i = 0;
      const targetDurationMs = 2000; // Target duration for character animation
      const charsPerStep = 5; // Render 5 characters at a time
      const numberOfSteps = content.length > 0 ? Math.ceil(content.length / charsPerStep) : 1;
      const calculatedInterval = numberOfSteps > 0 ? Math.max(1, targetDurationMs / numberOfSteps) : 8;

      intervalId = setInterval(() => {
        const nextI = Math.min(i + charsPerStep, content.length);
        setDisplayed(content.slice(0, nextI));
        i = nextI;
        if (i >= content.length) clearInterval(intervalId);
      }, calculatedInterval);

    } else if (animationMode === 'paragraph') {
      // Split by double newline, filter empty strings
      const paragraphs = content.split(/\n\s*\n/).filter(p => p.trim().length > 0);
      let currentParagraphIndex = 0;
      const targetDurationMs = 3000; // Target duration for paragraph animation (adjust as needed)
      const calculatedInterval = paragraphs.length > 0 ? Math.max(50, targetDurationMs / paragraphs.length) : 500; // Ensure minimum delay

      intervalId = setInterval(() => {
        if (currentParagraphIndex < paragraphs.length) {
          // Join paragraphs revealed so far
          setDisplayed(paragraphs.slice(0, currentParagraphIndex + 1).join('\n\n'));
          currentParagraphIndex++;
        } else {
          clearInterval(intervalId);
        }
      }, calculatedInterval);
    }

    // Cleanup function
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [content, animationMode]); // Depend on content and animationMode

  if (loading) return <Box sx={{ textAlign: 'center', py: 4 }}><CircularProgress /></Box>;
  if (error) return <Box sx={{ color: 'error.main', py: 2 }}>{error}</Box>;

  // Define plugins: remarkGfm and our custom plugin with the ref-updating callback
  // Cast the tuple to 'any' as a workaround for complex type inference issues with PluggableList
  // Pass the onHeadingsExtracted prop directly to the plugin options
  const remarkPluginsWithOptions = [
    remarkGfm,
    // Ensure the callback exists before passing it
    ...(onHeadingsExtracted ? [[remarkExtractHeadings, { onHeadingsExtracted }] as any] : [])
  ];

  return (
    <Box sx={{ fontSize: '1rem', lineHeight: 1.7, px: 1 }}>
      <ReactMarkdown
        remarkPlugins={remarkPluginsWithOptions}
        rehypePlugins={[rehypeSlug]} // Add rehype-slug here
      >
        {displayed}
      </ReactMarkdown>
    </Box>
  );
};
