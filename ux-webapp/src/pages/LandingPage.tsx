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
// Removed FlightTakeoffIcon and ShieldIcon imports
import ShuffleIcon from '@mui/icons-material/Shuffle';
import { fetchCustomerIds } from '../utils/fetchCustomerIds';
import { useNavigate } from 'react-router-dom';
import '../global.css';

const tagline = 'Travel Insurance Made Simple. Finally.'; // Updated tagline

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
  // Removed dropdownTop, dropdownLeft state
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

  // Removed updateDropdownPosition function and the useEffect hook that called it

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
      {/* New container Box to stack dropdown and card */}
      <Box sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        zIndex: 2,
        width: '100%', // Add width constraint
        maxWidth: 420   // Add maxWidth constraint (same as card)
      }}>
        {/* Subtle dropdown for MVP/demo only - MOVED HERE (Above Card) */}
        {showDropdown && (
          <Box
            sx={{
              mb: 2, // Margin below dropdown
              width: '100%', // Take full width of container
              maxWidth: 420, // Match card width
              bgcolor: 'background.paper',
              borderRadius: 1,
              boxShadow: 1,
              opacity: 0.9,
              p: 1.2,
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center', // Center items within dropdown box
              border: `1px solid ${theme.palette.divider}`,
              fontSize: 13,
            }}
          >
            <FormControl fullWidth size="small" sx={{ m: 0 }}>
              <InputLabel
                id="customer-select-label-demo"
                sx={{ fontSize: 13, top: '-6px', left: '-2px', bgcolor: 'background.paper', px: 0.5 }}
                shrink
              >
                Customer ID (Demo)
              </InputLabel>
              <Select
                labelId="customer-select-label-demo"
                value={selectedCustomer}
                label="Customer ID (Demo)"
                onChange={handleDropdownChange}
                sx={{ fontSize: 13, minHeight: 36, background: 'background.paper' }}
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
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, width: '100%', mt: 1, mb: 0.5 }}>
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
        {/* Main Login Card */}
        <Card ref={cardRef} sx={{ p: 4, width: '100%', maxWidth: 420, boxShadow: 3 /* Removed zIndex */ }}>
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', mb: 2 }}>
            {/* Replaced ShieldIcon with img tag */}
            <img
              src="/assets/aegis-shield.jpeg" /* Corrected extension */
              alt="Aegis AI Shield Logo"
              style={{ width: 48, height: 48, marginBottom: theme.spacing(1) }}
            />
          <Typography variant="h5" fontWeight={700} gutterBottom>
            Aegis AI {/* Updated Title */}
          </Typography>
          <Typography variant="subtitle1" color="text.secondary" gutterBottom align="center">
            {tagline}
          </Typography>
        </Box>
        <CardContent>
          {/* Dropdown removed from here */}
          <TextField
            label="Customer ID"
            value={inputValue}
            onChange={handleInputChange}
            fullWidth
            error={!!error}
            helperText={error || ''} // Removed default helper text
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
          {/* Updated caption below button, split into two lines */}
          <Typography variant="caption" color="text.secondary" display="block" align="center" sx={{ mt: 2, mb: 0.5 }}>
            Your Perfect Trip Deserves Perfect Coverage.
          </Typography>
          <Typography variant="caption" color="text.secondary" display="block" align="center">
            Login To View Your Personalized Report.
          </Typography>
        </CardContent>
      </Card>
      </Box> {/* End of new container Box */}
      <Box sx={{ position: 'fixed', bottom: 16, width: '100%' }}>
        <Typography variant="body2" color="text.secondary" align="center">
          &copy; {new Date().getFullYear()} Aegis AI. Powered by AI Reasoning System. {/* Updated Copyright */}
        </Typography>
      </Box>
    </Box>
  );
};

export default LandingPage;
