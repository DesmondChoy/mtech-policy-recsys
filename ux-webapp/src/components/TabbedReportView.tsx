import React, { useState, useEffect } from 'react'; // Added useEffect
import { Box, AppBar, Tabs, Tab, Toolbar, Typography, Button, MenuItem, Select, FormControl, InputLabel, CircularProgress } from '@mui/material'; // Added CircularProgress
import DescriptionIcon from '@mui/icons-material/Description';
import CompareIcon from '@mui/icons-material/Compare';
import AssignmentIndIcon from '@mui/icons-material/AssignmentInd';
import ChatIcon from '@mui/icons-material/Chat';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import { MarkdownRenderer } from './MarkdownRenderer';
import { JsonPrettyViewer } from './JsonPrettyViewer';
import { TranscriptViewer } from './TranscriptViewer'; // Import the new component
// import { PdfViewer } from './PdfViewer'; // Comment out for now

export interface TabbedReportViewProps {
  uuid: string;
  // insurers: string[]; // Removed
  // insurerPdfMap: Record<string, string>; // Removed
  onSwitchCustomer: () => void;
}

const tabLabels = [
  { label: 'Recommendation', icon: <DescriptionIcon /> },
  { label: 'Policy Comparison', icon: <CompareIcon /> },
  { label: 'Customer Requirements', icon: <AssignmentIndIcon /> },
  { label: 'Transcript', icon: <ChatIcon /> },
  // { label: 'Policy PDFs', icon: <PictureAsPdfIcon /> }, // Comment out for now
];

// Helper function to extract insurer name from filename
const extractInsurerFromFilename = (filename: string): string | null => {
  const match = filename.match(/^policy_comparison_report_([^_]+)(?:_[a-f0-9-]+)?\.md$/i);
  return match ? match[1] : null;
};


export const TabbedReportView: React.FC<TabbedReportViewProps> = ({ uuid, onSwitchCustomer }) => {
  const [tabIndex, setTabIndex] = useState(0);
  const [availableInsurers, setAvailableInsurers] = useState<string[]>([]);
  const [selectedInsurer, setSelectedInsurer] = useState<string>('');
  const [loadingInsurers, setLoadingInsurers] = useState(true);
  const [insurerError, setInsurerError] = useState<string | null>(null);
  // State for scenario name
  const [scenarioName, setScenarioName] = useState<string | null>(null);
  const [loadingScenario, setLoadingScenario] = useState(true);
  const [scenarioError, setScenarioError] = useState<string | null>(null);


  // Effect to load available insurers from results index
  useEffect(() => {
    if (!uuid) return;

    setLoadingInsurers(true);
    setInsurerError(null);
    setAvailableInsurers([]);
    setSelectedInsurer('');

    const controller = new AbortController();
    const indexUrl = `/results/${uuid}/index.json`;

    fetch(indexUrl, { signal: controller.signal })
      .then(res => {
        if (!res.ok) throw new Error(`Could not fetch insurer index at ${indexUrl}`);
        return res.json();
      })
      .then((reportFilenames: string[]) => {
        const insurersFound = reportFilenames
          .map(extractInsurerFromFilename)
          .filter((name): name is string => name !== null) // Filter out nulls and type guard
          .sort(); // Sort alphabetically

        if (insurersFound.length === 0) {
          throw new Error('No comparison reports found for this customer.');
        }
        setAvailableInsurers(insurersFound);
        setSelectedInsurer(insurersFound[0]); // Select the first one by default
      })
      .catch(err => {
         if (err.name === 'AbortError') return;
         console.error("Error fetching or processing insurer index:", err);
         setInsurerError('Failed to load available insurers.');
      })
      .finally(() => setLoadingInsurers(false));

      return () => controller.abort();

  }, [uuid]);

  // Effect to load scenario name from transcript index
   useEffect(() => {
    if (!uuid) return;

    setLoadingScenario(true);
    setScenarioError(null);
    setScenarioName(null);

    const controller = new AbortController();
    const transcriptIndexUrl = '/transcripts_index.json';

    fetch(transcriptIndexUrl, { signal: controller.signal })
      .then(res => {
        if (!res.ok) throw new Error(`Could not fetch transcript index at ${transcriptIndexUrl}`);
        return res.json();
      })
      .then((index: Record<string, string>) => {
        const transcriptFilename = index[uuid];
        if (!transcriptFilename) throw new Error(`UUID ${uuid} not found in transcript index.`);

        // Extract scenario name (handle 'no_scenario')
        // Regex: Match 'parsed_transcript_' followed by the scenario name (non-greedy), then '_' and the UUID pattern, ending with '.json'
        const scenarioMatch = transcriptFilename.match(/^parsed_transcript_(.*?)_[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}\.json$/i);
        const extractedScenario = scenarioMatch ? scenarioMatch[1] : null;

        if (!extractedScenario) {
            console.warn(`Could not extract scenario name from filename: ${transcriptFilename}`);
            // Fallback or decide how to handle - maybe assume 'no_scenario' or a default?
            // For now, let's allow null and handle path construction later.
             setScenarioName(null); // Or set a default like 'unknown_scenario'
             throw new Error(`Could not parse scenario name from: ${transcriptFilename}`);
        } else {
             setScenarioName(extractedScenario);
        }
      })
      .catch(err => {
         if (err.name === 'AbortError') return;
         console.error("Error fetching or processing transcript index:", err);
         setScenarioError('Failed to load scenario information.');
      })
      .finally(() => setLoadingScenario(false));

      return () => controller.abort();

  }, [uuid]);


  // File paths (now depend on selectedInsurer and scenarioName state)
  const recommendationPath = `/results/${uuid}/recommendation_report_${uuid}.md`;
  const policyComparisonPath = selectedInsurer ? `/results/${uuid}/policy_comparison_report_${selectedInsurer}_${uuid}.md` : '';
  // Construct paths only if scenarioName is loaded
  const requirementsPath = scenarioName ? `/data/extracted_customer_requirements/requirements_${scenarioName}_${uuid}.json` : '';
  const transcriptPath = scenarioName ? `/data/transcripts/processed/parsed_transcript_${scenarioName}_${uuid}.json` : '';

  // Determine if main content is ready (insurers and scenario loaded without error)
  const isContentReady = !loadingInsurers && !insurerError && !loadingScenario && !scenarioError;
  const isLoading = loadingInsurers || loadingScenario;
  const hasError = insurerError || scenarioError;


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
          allowScrollButtonsMobile // Ensure scroll buttons are visible on mobile if needed
        >
          {tabLabels.map((tab) => (
            <Tab key={tab.label} label={tab.label} icon={tab.icon} iconPosition="start" />
          ))}
        </Tabs>
      </AppBar>
      <Box sx={{ p: 3 }}>
        {tabIndex === 0 && (
          <MarkdownRenderer filePath={recommendationPath} animationMode="character" /> // Use animationMode
        )}
        {tabIndex === 1 && (
          <Box>
            {loadingInsurers ? (
              <CircularProgress size={24} />
            ) : insurerError ? (
               <Typography color="error">{insurerError}</Typography>
            ) : (
              <FormControl sx={{ mb: 2, minWidth: 240 }} disabled={availableInsurers.length === 0}>
                <InputLabel id="insurer-select-label">Insurer</InputLabel>
                <Select
                  labelId="insurer-select-label"
                  value={selectedInsurer}
                  label="Insurer"
                  onChange={e => setSelectedInsurer(e.target.value as string)}
                >
                  {availableInsurers.map(insurer => (
                    <MenuItem key={insurer} value={insurer}>{insurer}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            )}
            {policyComparisonPath ? (
               <MarkdownRenderer filePath={policyComparisonPath} animationMode="paragraph" /> // Use animationMode
            ) : !loadingInsurers && !insurerError ? (
               <Typography>Select an insurer to view the comparison.</Typography>
            ) : null}
          </Box>
        )}
         {tabIndex === 2 && (
            isLoading ? <CircularProgress size={24} /> :
            hasError ? <Typography color="error">{scenarioError || 'Error loading data.'}</Typography> :
            requirementsPath ? <JsonPrettyViewer filePath={requirementsPath} dataPath="json_dict" /> : // Added dataPath prop
            <Typography>Could not determine requirements file path.</Typography>
        )}
        {tabIndex === 3 && (
            isLoading ? <CircularProgress size={24} /> :
            hasError ? <Typography color="error">{scenarioError || 'Error loading data.'}</Typography> :
            transcriptPath ? <TranscriptViewer filePath={transcriptPath} /> : // Use TranscriptViewer instead of JsonPrettyViewer
            <Typography>Could not determine transcript file path.</Typography>
        )}
        {/* {tabIndex === 4 && isContentReady && ( // Comment out PDF tab for now
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
            {availableInsurers.map(insurer => (
              <Box key={insurer} sx={{ width: 340 }}>
                <Typography variant="subtitle1" sx={{ mb: 1 }}>{insurer}</Typography>
                {/* Need to dynamically determine PDF path, e.g., assuming /data/policies/raw/INSURER.pdf */}
                {/* <PdfViewer filePath={`/data/policies/raw/${insurer}.pdf`} /> */}
              {/* </Box>
            ))}
          </Box>
        )} */}
      </Box>
    </Box>
  );
};
