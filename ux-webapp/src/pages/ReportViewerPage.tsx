import React, { useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { TabbedReportView } from '../components/TabbedReportView';

const ReportViewerPage: React.FC = () => {
  const { reportId } = useParams<{ reportId: string }>();
  const navigate = useNavigate();
  const uuid = reportId || '';

  // Memoize props for performance
  const tabProps = useMemo(() => ({
    uuid,
    // insurers and insurerPdfMap removed - will be handled dynamically in TabbedReportView
    onSwitchCustomer: () => navigate('/')
  }), [uuid, navigate]);

  if (!uuid) return <div>No customer selected.</div>;
  return <TabbedReportView {...tabProps} />; // Pass only uuid and onSwitchCustomer
};

export default ReportViewerPage;
