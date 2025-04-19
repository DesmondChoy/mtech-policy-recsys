import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Button, Typography, Paper, CircularProgress } from '@mui/material';
import ChatBubble from '../components/ChatBubble';

interface TranscriptEntry {
  speaker: string;
  dialogue: string;
}

const TranscriptPage: React.FC = () => {
  const { uuid } = useParams<{ uuid: string }>();
  const [transcript, setTranscript] = useState<TranscriptEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    if (!uuid) return;
    setLoading(true);
    setError('');
    // Step 1: Fetch the transcripts index to map UUID to filename
    fetch('/transcripts_index.json')
      .then(res => res.ok ? res.json() : Promise.reject('Index not found'))
      .then((index: Record<string, string>) => {
        const fileName = index[uuid];
        if (!fileName) throw new Error('Transcript not found.');
        // Step 2: Fetch the actual transcript file
        return fetch(`/data/transcripts/processed/${fileName}`)
          .then(res => res.ok ? res.json() : Promise.reject('Transcript not found.'));
      })
      .then(data => setTranscript(data))
      .catch(() => setError('Transcript not found.'))
      .finally(() => setLoading(false));
  }, [uuid]);

  const handleYes = () => navigate(`/transition/${uuid}`);
  const handleNo = () => navigate(`/`);

  return (
    <Box sx={{ maxWidth: 600, mx: 'auto', mt: 6, px: 2 }}>
      <Paper elevation={3} sx={{ p: 2, mb: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'sticky', top: 0, zIndex: 2 }}>
        <Typography variant="subtitle1" fontWeight={600}>Is this your transcript?</Typography>
        <Box>
          <Button variant="contained" color="primary" onClick={handleYes} sx={{ mr: 1 }}>Yes</Button>
          <Button variant="outlined" color="secondary" onClick={handleNo}>No</Button>
        </Box>
      </Paper>
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}><CircularProgress /></Box>
      ) : error ? (
        <Typography color="error">{error}</Typography>
      ) : (
        <Box>
          {transcript.map((entry, idx) => (
            <ChatBubble key={idx} speaker={entry.speaker} dialogue={entry.dialogue} />
          ))}
        </Box>
      )}
    </Box>
  );
};

export default TranscriptPage;
