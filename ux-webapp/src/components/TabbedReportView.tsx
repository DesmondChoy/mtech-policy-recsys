import React, { useState } from 'react';
import { Box, AppBar, Tabs, Tab, Toolbar, Typography, Button, MenuItem, Select, FormControl, InputLabel } from '@mui/material';
import DescriptionIcon from '@mui/icons-material/Description';
import CompareIcon from '@mui/icons-material/Compare';
import AssignmentIndIcon from '@mui/icons-material/AssignmentInd';
import ChatIcon from '@mui/icons-material/Chat';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import { MarkdownRenderer } from './MarkdownRenderer';
import { JsonPrettyViewer } from './JsonPrettyViewer';
import { PdfViewer } from './PdfViewer';

export interface TabbedReportViewProps {
  uuid: string;
  insurers: string[];
  insurerPdfMap: Record<string, string>; // insurer name -> PDF file path
  onSwitchCustomer: () => void;
}

const tabLabels = [
  { label: 'Recommendation', icon: <DescriptionIcon /> },
  { label: 'Policy Comparison', icon: <CompareIcon /> },
  { label: 'Customer Requirements', icon: <AssignmentIndIcon /> },
  { label: 'Transcript', icon: <ChatIcon /> },
  { label: 'Policy PDFs', icon: <PictureAsPdfIcon /> },
];

export const TabbedReportView: React.FC<TabbedReportViewProps> = ({ uuid, insurers, insurerPdfMap, onSwitchCustomer }) => {
  const [tabIndex, setTabIndex] = useState(0);
  const [selectedInsurer, setSelectedInsurer] = useState(insurers[0] || '');

  // File paths
  const recommendationPath = `/results/${uuid}/recommendation_report_${uuid}.md`;
  const policyComparisonPath = `/results/${uuid}/policy_comparison_report_${selectedInsurer}.md`;
  const requirementsPath = `/data/extracted_customer_requirements/requirements_${uuid}.json`;
  const transcriptPath = `/data/transcripts/raw/synthetic/transcript_${uuid}.json`;

  return (
    <Box sx={{ width: '100%', bgcolor: 'background.paper' }}>
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Policy Recommendation Report
          </Typography>
          <Button color="primary" variant="outlined" onClick={onSwitchCustomer} sx={{ ml: 2 }}>
            Switch Customer
          </Button>
        </Toolbar>
        <Tabs
          value={tabIndex}
          onChange={(_, idx) => setTabIndex(idx)}
          indicatorColor="primary"
          textColor="primary"
          variant="scrollable"
          scrollButtons="auto"
        >
          {tabLabels.map((tab) => (
            <Tab key={tab.label} label={tab.label} icon={tab.icon} iconPosition="start" />
          ))}
        </Tabs>
      </AppBar>
      <Box sx={{ p: 3 }}>
        {tabIndex === 0 && (
          <MarkdownRenderer filePath={recommendationPath} animate />
        )}
        {tabIndex === 1 && (
          <Box>
            <FormControl sx={{ mb: 2, minWidth: 240 }}>
              <InputLabel id="insurer-select-label">Insurer</InputLabel>
              <Select
                labelId="insurer-select-label"
                value={selectedInsurer}
                label="Insurer"
                onChange={e => setSelectedInsurer(e.target.value as string)}
              >
                {insurers.map(insurer => (
                  <MenuItem key={insurer} value={insurer}>{insurer}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <MarkdownRenderer filePath={policyComparisonPath} />
          </Box>
        )}
        {tabIndex === 2 && (
          <JsonPrettyViewer filePath={requirementsPath} />
        )}
        {tabIndex === 3 && (
          <JsonPrettyViewer filePath={transcriptPath} />
        )}
        {tabIndex === 4 && (
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
            {insurers.map(insurer => (
              <Box key={insurer} sx={{ width: 340 }}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>{insurer}</Typography>
                <PdfViewer filePath={insurerPdfMap[insurer]} />
              </Box>
            ))}
          </Box>
        )}
      </Box>
    </Box>
  );
};
