import React, { useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { TabbedReportView } from '../components/TabbedReportView';

// Example insurers and PDF mapping (replace with dynamic loading if needed)
const insurers = ['FWD', 'AIG', 'Allianz', 'Sompo'];
const insurerPdfMap = {
  FWD: '/data/policies/raw/FWD.pdf',
  AIG: '/data/policies/raw/AIG.pdf',
  Allianz: '/data/policies/raw/Allianz.pdf',
  Sompo: '/data/policies/raw/Sompo.pdf',
};

const ReportViewerPage: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();
  const uuid = reportId || '';

  // Memoize props for performance
  const tabProps = useMemo(() => ({
    uuid,
    insurers,
    insurerPdfMap,
    onSwitchCustomer: () => navigate('/')
  }), [uuid, navigate]);

  if (!uuid) return <div>No customer selected.</div>;
  return <TabbedReportView {...tabProps} />;
};

export default ReportViewerPage;
