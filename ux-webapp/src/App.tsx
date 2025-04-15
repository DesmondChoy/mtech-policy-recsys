import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import DashboardPage from './pages/DashboardPage';
import ReportViewerPage from './pages/ReportViewerPage';
import Container from '@mui/material/Container';

function App() {
  return (
    <Router>
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/report/:reportId" element={<ReportViewerPage />} />
        </Routes>
      </Container>
    </Router>
  );
}

export default App;
