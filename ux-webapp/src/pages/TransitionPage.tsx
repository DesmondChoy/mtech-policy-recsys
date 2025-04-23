import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, Typography, CircularProgress, useTheme } from '@mui/material';
import { keyframes } from '@emotion/react';

// --- Message Phases ---
const loadingPhases: string[][] = [
  // 1. Extracting User Requirements
  [
    'Parsing transcript for hidden gems...',
    'Mining insights from your conversation...',
    'Untangling your travel priorities...',
    'Summarizing your coverage wishlist...',
    'Listening for subtle hints in your transcript...',
    'Detecting preferences with our AI super-sleuth...',
    'Reading between the lines for hidden priorities...',
    'Translating your words into actionable needs...'
  ],
  // 2. Extracting Policy Details
  [
    'Evaluating policy fine print (so you don’t have to)...',
    'Decoding insurance jargon into plain English...',
    'Ensuring your adventure is fully covered...',
    'Sifting through policy PDFs so you don’t have to...',
    'Peeking under the hood of every policy...',
    'Reticulating exclusions and inclusions...',
    'Hunting for secret clauses (no magnifying glass required)...',
    'Making sense of the small print, one clause at a time...'
  ],
  // 3. Comparing Policies
  [
    'Verifying policy benefits (and exclusions!)...',
    'Checking for lost luggage (in the data)...',
    'Double-checking emergency evacuation routes...',
    'Launching the ultimate policy face-off...',
    'Scoring policies for your peace of mind...',
    'Running a policy relay race (may the best win)...',
    'Matching your needs to the perfect policy partner...',
    'Consulting our virtual actuaries...'
  ],
  // 4. Generating Personalized Recommendations
  [
    'Generating your personalized recommendations...',
    'Crunching numbers for your peace of mind...',
    'Optimizing recommendations for your adventure...',
    'Tailoring advice to your unique journey...',
    'Handpicking the best options for you...',
    'Packing your personalized report with insights...',
    'Finalizing your travel insurance playbook...',
    'Making sure your bases (and bags) are covered...'
  ]
];

const PHASE_DURATION = 2000; // ms per phase (increased to 2s)

// Material UI palette shimmer keyframes
const muiShimmer = keyframes`
  0% {
    background-position: 0% 50%;
  }
  100% {
    background-position: 100% 50%;
  }
`;

// Pulsing dots animation
const dots = keyframes`
  0%, 80%, 100% {
    opacity: 0;
  }
  40% {
    opacity: 1;
  }
`;

const PulsingDots: React.FC = () => (
  <span style={{ display: 'inline-block', width: 24 }}>
    <span style={{
      animation: `${dots} 1s infinite`,
      animationDelay: '0s',
      color: 'inherit',
      fontWeight: 700,
    }}>.</span>
    <span style={{
      animation: `${dots} 1s infinite`,
      animationDelay: '0.2s',
      color: 'inherit',
      fontWeight: 700,
    }}>.</span>
    <span style={{
      animation: `${dots} 1s infinite`,
      animationDelay: '0.4s',
      color: 'inherit',
      fontWeight: 700,
    }}>.</span>
  </span>
);

const TransitionPage: React.FC = () => {
  const { uuid } = useParams<{ uuid: string }>();
  const navigate = useNavigate();
  const theme = useTheme();
  const [phase, setPhase] = useState(0);
  const [message, setMessage] = useState(loadingPhases[0][0]);

  // Use Material UI palette for shimmer
  const shimmerStyle = {
    background: `linear-gradient(90deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main}, ${theme.palette.primary.light})`,
    backgroundSize: '300% 100%',
    backgroundClip: 'text',
    WebkitBackgroundClip: 'text',
    color: 'transparent',
    WebkitTextFillColor: 'transparent',
    animation: `${muiShimmer} 2.5s linear infinite`,
    fontWeight: 600,
    fontSize: '1.5rem', // Increased font size
    letterSpacing: 0.2,
    minHeight: 32,
  } as React.CSSProperties;

  useEffect(() => {
    if (phase < loadingPhases.length) {
      // Pick a random message for the current phase
      const messages = loadingPhases[phase];
      setMessage(messages[Math.floor(Math.random() * messages.length)]);
      const timer = setTimeout(() => setPhase((prev) => prev + 1), PHASE_DURATION);
      return () => clearTimeout(timer);
    } else {
      // After last phase, navigate to the disclaimer page
      const navTimeout = setTimeout(() => {
        navigate(`/disclaimer/${uuid}`); // Navigate to disclaimer page
      }, PHASE_DURATION);
      return () => clearTimeout(navTimeout);
    }
  }, [phase, uuid, navigate]);

  return (
    <Box sx={{ minHeight: '60vh', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center' }}>
      <CircularProgress sx={{ mb: 3 }} />
      <Typography
        variant="h6"
        sx={{ ...shimmerStyle, textAlign: 'center' }} // Added textAlign: 'center'
        component="span"
      >
        {message}
        <PulsingDots />
      </Typography>
    </Box>
  );
};

export default TransitionPage;
