import React, { useEffect, useState } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import ChatBubble from './ChatBubble'; // Reuse the existing ChatBubble component

interface TranscriptEntry {
  speaker: string;
  dialogue: string;
}

// Define the expected structure of the JSON file content
interface TranscriptFileContent {
  // Assuming the file contains an object with a 'transcript' key holding the array
  // Adjust this if the structure is different (e.g., if the file is just the array directly)
  transcript: TranscriptEntry[];
  // Add other potential top-level keys if they exist, like scenario, uuid etc.
  scenario?: string | null;
  uuid?: string;
}

export const TranscriptViewer: React.FC<{ filePath: string }> = ({ filePath }) => {
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setLoading(true);
    setError(null);
    setTranscript([]); // Reset transcript
    const controller = new AbortController();

    fetch(filePath, { signal: controller.signal })
      .then(res => {
        if (!res.ok) throw new Error(`File not found at ${filePath}`);
        return res.json();
      })
      .then((data: TranscriptFileContent | TranscriptEntry[]) => { // Handle both possible root structures
        let entries: TranscriptEntry[] = [];
        // Check if the data is an object with a 'transcript' key or just the array itself
        if (Array.isArray(data)) {
          entries = data;
        } else if (data && Array.isArray(data.transcript)) {
          entries = data.transcript;
        } else {
          // Handle unexpected structure
          console.error("Unexpected transcript file structure:", data);
          throw new Error("Transcript data is not in the expected format (array or object with 'transcript' key).");
        }

        // Validate entries have speaker and dialogue
        if (entries.some(entry => typeof entry.speaker !== 'string' || typeof entry.dialogue !== 'string')) {
            throw new Error("Transcript entries are missing 'speaker' or 'dialogue' properties.");
        }

        setTranscript(entries);
      })
      .catch(err => {
        if (err.name === 'AbortError') return;
        console.error(`Error loading/processing transcript from ${filePath}:`, err);
        setError(err.message || 'Failed to load or process transcript file.');
      })
      .finally(() => setLoading(false));

      return () => controller.abort();
  }, [filePath]);

  if (loading) return <Box sx={{ textAlign: 'center', py: 4 }}><CircularProgress /></Box>;
  if (error) return <Typography color="error" sx={{ py: 2 }}>{error}</Typography>;
  if (transcript.length === 0) return <Typography sx={{ py: 2 }}>No transcript entries found.</Typography>;

  return (
    <Box>
      {transcript.map((entry, idx) => (
        <ChatBubble key={idx} speaker={entry.speaker} dialogue={entry.dialogue} />
      ))}
    </Box>
  );
};
