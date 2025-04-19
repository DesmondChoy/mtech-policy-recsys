import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import DashboardPage from './pages/DashboardPage';
import ReportViewerPage from './pages/ReportViewerPage';
import TranscriptPage from './pages/TranscriptPage';
import TransitionPage from './pages/TransitionPage';
import Container from '@mui/material/Container';

function App() {
  return (
    <Router>
      <Container maxWidth="md" sx={{ py: 4, background: 'transparent', minHeight: '100vh' }}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/report/:reportId" element={<ReportViewerPage />} />
          <Route path="/transcript/:uuid" element={<TranscriptPage />} />
          <Route path="/transition/:uuid" element={<TransitionPage />} />
        </Routes>
      </Container>
    </Router>
  );
}

export default App;
