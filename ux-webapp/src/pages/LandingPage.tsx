import React, { useState, useEffect } from 'react';
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
  useTheme
} from '@mui/material';
import FlightTakeoffIcon from '@mui/icons-material/FlightTakeoff';
import { fetchCustomerIds } from '../utils/fetchCustomerIds';
import '../global.css';

const tagline = 'Your journey, your coverage. Compare, understand, and choose with confidence.';

const LandingPage: React.FC = () => {
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [customerIds, setCustomerIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const theme = useTheme();

  useEffect(() => {
    fetchCustomerIds()
      .then(ids => {
        console.log('Loaded customer IDs:', ids);
        setCustomerIds(ids);
      })
      .catch((err) => {
        console.error('Error loading customer IDs:', err);
        setCustomerIds([]);
      })
      .finally(() => setLoading(false));
  }, []);

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
      <Card sx={{ p: 4, width: '100%', maxWidth: 420, boxShadow: 3, zIndex: 2 }}>
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
          <FormControl fullWidth sx={{ mb: 2 }}>
            <InputLabel id="customer-select-label">Customer ID</InputLabel>
            <Select
              labelId="customer-select-label"
              value={selectedCustomer}
              label="Customer ID"
              onChange={e => setSelectedCustomer(e.target.value)}
            >
              {customerIds.length === 0 && !loading ? (
                <MenuItem value="" disabled>
                  No customer IDs found
                </MenuItem>
              ) : (
                customerIds.map(id => (
                  <MenuItem key={id} value={id}>{id}</MenuItem>
                ))
              )}
            </Select>
          </FormControl>
          <Button
            variant="contained"
            color="primary"
            fullWidth
            disabled={!selectedCustomer || loading}
            sx={{ mt: 1 }}
            onClick={() => {
              if (selectedCustomer) {
                window.location.href = `/report/${selectedCustomer}`;
              }
            }}
          >
            Continue
          </Button>
          <Typography variant="caption" color="text.secondary" display="block" align="center" sx={{ mt: 2 }}>
            Select your customer profile to view your personalized recommendations.
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
