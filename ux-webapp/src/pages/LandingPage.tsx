import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  TextField,
  useTheme,
  IconButton,
  Tooltip
} from '@mui/material';
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff';
import ShuffleIcon from '@mui/icons-material/Shuffle';
import { fetchCustomerIds } from '../utils/fetchCustomerIds';
import { useNavigate } from 'react-router-dom';
import '../global.css';

const tagline = 'Your journey, your coverage. Compare, understand, and choose with confidence.';

// const isDemo = import.meta.env.MODE !== 'production'; // Removed unused variable

const LandingPage: React.FC = () => {
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [customerIds, setCustomerIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [inputValue, setInputValue] = useState('');
  const [showDropdown, setShowDropdown] = useState(true); // Controls dropdown visibility
  const [error, setError] = useState('');
  const theme = useTheme();
  const cardRef = useRef<HTMLDivElement>(null);
  const [dropdownTop, setDropdownTop] = useState<number | undefined>(undefined);
  const [dropdownLeft, setDropdownLeft] = useState<number | undefined>(undefined);
  const navigate = useNavigate();

  useEffect(() => {
    fetchCustomerIds()
      .then(ids => {
        setCustomerIds(ids);
      })
      .catch(() => {
        setCustomerIds([]);
      })
      .finally(() => setLoading(false));
  }, []);

  // Helper to update dropdown position
  const updateDropdownPosition = () => {
    if (cardRef.current) {
      const rect = cardRef.current.getBoundingClientRect();
      setDropdownTop(rect.top);
      setDropdownLeft(rect.right + 16); // 16px gap from card
    }
  };

  useEffect(() => {
    updateDropdownPosition();
    window.addEventListener('resize', updateDropdownPosition);
    return () => window.removeEventListener('resize', updateDropdownPosition);
  }, [loading]);

  // Validate input on change
  useEffect(() => {
    if (!inputValue) {
      setError('');
    } else if (!customerIds.includes(inputValue)) {
      setError('User not found');
    } else {
      setError('');
    }
  }, [inputValue, customerIds]);

  const handleDropdownChange = (e: any) => {
    setSelectedCustomer(e.target.value);
    setInputValue(e.target.value);
    setError('');
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setInputValue(e.target.value);
    setSelectedCustomer(e.target.value);
  };

  const handleContinue = () => {
    if (!inputValue || !customerIds.includes(inputValue)) {
      setError('User not found');
      return;
    }
    setShowDropdown(false); // Hide dropdown after continue
    navigate(`/transcript/${inputValue}`);
  };

  const handleRandomPick = () => {
    if (customerIds.length === 0) return;
    const randomId = customerIds[Math.floor(Math.random() * customerIds.length)];
    setSelectedCustomer(randomId);
    setInputValue(randomId);
    setError('');
  };

  return (
    <Box
      sx={{
        height: '100vh',
        width: '100vw',
        position: 'fixed',
        top: 0,
        left: 0,
        zIndex: 0,
        overflow: 'hidden',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: `radial-gradient(circle at 70% 20%, ${theme.palette.primary.light} 0%, transparent 60%),\n                     radial-gradient(circle at 20% 80%, #b2ebf2 0%, transparent 70%),\n                     linear-gradient(135deg, #e3f2fd 0%, #b3c6f7 100%)`
      }}
    >
      {/* Decorative SVG background pattern (pointerEvents: none!) */}
      <svg
        width="900"
        height="900"
        viewBox="0 0 900 900"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{ position: 'absolute', top: -120, left: -120, opacity: 0.09, zIndex: 0, pointerEvents: 'none' }}
      >
        <circle cx="450" cy="450" r="400" fill="#90caf9" />
        <rect x="200" y="650" width="500" height="60" rx="30" fill="#b2ebf2" />
        <rect x="650" y="200" width="60" height="500" rx="30" fill="#b2ebf2" />
      </svg>
      {/* Subtle right-aligned dropdown for MVP/demo only */}
      {showDropdown && (
        <Box
          sx={{
            position: 'fixed',
            top: dropdownTop !== undefined ? dropdownTop : 28,
            left: dropdownLeft !== undefined ? dropdownLeft : 'auto',
            minWidth: 140,
            maxWidth: 180,
            bgcolor: 'rgba(255,255,255,0.75)',
            borderRadius: 2,
            boxShadow: 1,
            opacity: 0.72,
            zIndex: 10,
            p: 1.2,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            border: '1px solid #e3e3e3',
            fontSize: 13,
          }}
        >
          <FormControl fullWidth size="small" sx={{ m: 0 }}>
            <InputLabel
              id="customer-select-label-demo"
              sx={{ fontSize: 13, top: '-6px', left: '-2px', bgcolor: 'rgba(255,255,255,0.75)', px: 0.5 }}
              shrink
            >
              Customer ID (Demo)
            </InputLabel>
            <Select
              labelId="customer-select-label-demo"
              value={selectedCustomer}
              label="Customer ID (Demo)"
              onChange={handleDropdownChange}
              sx={{ fontSize: 13, minHeight: 36, background: 'rgba(255,255,255,0.9)' }}
              MenuProps={{
                PaperProps: {
                  sx: { fontSize: 13, maxHeight: 200 }
                }
              }}
            >
              {customerIds.length === 0 && !loading ? (
                <MenuItem value="" disabled>
                  No customer IDs found
                </MenuItem>
              ) : (
                customerIds.map(id => (
                  <MenuItem key={id} value={id} sx={{ fontSize: 13 }}>
                    {id}
                  </MenuItem>
                ))
              )}
            </Select>
          </FormControl>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, width: '100%', mt: 1, mb: 0.5 }}>
            <Tooltip title="Pick Random Customer">
              <IconButton
                size="small"
                aria-label="random-customer"
                onClick={handleRandomPick}
                sx={{ color: 'primary.main', bgcolor: 'rgba(144,202,249,0.08)', '&:hover': { bgcolor: 'rgba(144,202,249,0.18)' }, mr: 0.5 }}
                disabled={customerIds.length === 0}
              >
                <ShuffleIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            <Typography variant="caption" color="text.secondary" sx={{ fontSize: 12, lineHeight: 1.2 }}>
              This dropdown is for MVP/demo only; will not appear in production.
            </Typography>
          </Box>
        </Box>
      )}
      <Card ref={cardRef} sx={{ p: 4, width: '100%', maxWidth: 420, boxShadow: 3, zIndex: 2 }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 2 }}>
          <FlightTakeoffIcon color="primary" sx={{ fontSize: 48, mb: 1 }} />
          <Typography variant="h5" fontWeight={700} gutterBottom>
            TravelSafe Recommender System
          </Typography>
          <Typography variant="subtitle1" color="text.secondary" gutterBottom align="center">
            {tagline}
          </Typography>
        </Box>
        <CardContent>
          <TextField
            label="Customer ID"
            value={inputValue}
            onChange={handleInputChange}
            fullWidth
            error={!!error}
            helperText={error || 'Enter or select your customer ID'}
            sx={{ mb: 2 }}
            autoFocus
          />
          <Button
            variant="contained"
            color="primary"
            fullWidth
            disabled={!inputValue || !!error || loading}
            sx={{ mt: 1 }}
            onClick={handleContinue}
          >
            Continue
          </Button>
          <Typography variant="caption" color="text.secondary" display="block" align="center" sx={{ mt: 2 }}>
            Select or enter your customer profile to view your personalized recommendations.
          </Typography>
        </CardContent>
      </Card>
      <Box sx={{ position: 'fixed', bottom: 16, width: '100%' }}>
        <Typography variant="body2" color="text.secondary" align="center">
          &copy; {new Date().getFullYear()} TravelSafe. Powered by AI Reasoning System.
        </Typography>
      </Box>
    </Box>
  );
};

export default LandingPage;
