import React, { useState, useEffect, useCallback, useRef } from 'react'; // Added useRef
import { Box, AppBar, Tabs, Tab, Toolbar, Typography, Button, MenuItem, Select, FormControl, InputLabel, CircularProgress, Drawer, IconButton, useTheme, useMediaQuery } from '@mui/material'; // Removed Grid, Added Drawer, IconButton, useTheme, useMediaQuery
import DescriptionIcon from '@mui/icons-material/Description';
import CompareIcon from '@mui/icons-material/Compare';
import AssignmentIndIcon from '@mui/icons-material/AssignmentInd';
import MenuIcon from '@mui/icons-material/Menu'; // Icon for mobile TOC toggle
import ChatIcon from '@mui/icons-material/Chat';
import FeedbackIcon from '@mui/icons-material/Feedback'; // Import Feedback icon
import { MarkdownRenderer } from './MarkdownRenderer';
import { JsonPrettyViewer } from './JsonPrettyViewer';
import { TranscriptViewer } from './TranscriptViewer';
import FeedbackTabContent from './FeedbackTabContent'; // Import FeedbackTabContent component
import TableOfContents from './TableOfContents'; // Import TOC component
import FeedbackButtons from './FeedbackButtons'; // Import FeedbackButtons component
import { type HeadingData } from './remark-extract-headings'; // Updated path after moving file

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
  { label: 'Feedback', icon: <FeedbackIcon /> }, // Add Feedback tab
  // { label: 'Policy PDFs', icon: <PictureAsPdfIcon /> }, // Comment out for now
];

// Helper function to extract insurer name from filename
const extractInsurerFromFilename = (filename: string): string | null => {
  const match = filename.match(/^policy_comparison_report_([^_]+)(?:_[a-f0-9-]+)?\.md$/i);
  return match ? match[1] : null;
};


export const TabbedReportView: React.FC<TabbedReportViewProps> = ({ uuid, onSwitchCustomer }) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md')); // Check for mobile screen size

  const [tabIndex, setTabIndex] = useState(0);
  const [availableInsurers, setAvailableInsurers] = useState<string[]>([]);
  const [selectedInsurer, setSelectedInsurer] = useState<string>('');
  const [loadingInsurers, setLoadingInsurers] = useState(true);
  const [insurerError, setInsurerError] = useState<string | null>(null);
  const [scenarioName, setScenarioName] = useState<string | null>(null);
  const [loadingScenario, setLoadingScenario] = useState(true);
  const [scenarioError, setScenarioError] = useState<string | null>(null);
  const [headings, setHeadings] = useState<HeadingData[]>([]); // State for TOC headings
  const [mobileTocOpen, setMobileTocOpen] = useState(false); // State for mobile drawer
  const headingUpdateTimeoutRef = useRef<number | null>(null); // Ref for debounce timeout ID

  // Debounced callback for MarkdownRenderer to update headings
  const handleHeadingsExtracted = useCallback((extractedHeadings: HeadingData[]) => {
    // Clear any existing timeout
    if (headingUpdateTimeoutRef.current !== null) {
      clearTimeout(headingUpdateTimeoutRef.current);
    }

    // Set a new timeout to update the state after a short delay
    headingUpdateTimeoutRef.current = window.setTimeout(() => {
      setHeadings(prevHeadings => {
        // Check again if update is needed (in case multiple calls happened quickly)
        if (JSON.stringify(prevHeadings) !== JSON.stringify(extractedHeadings)) {
          return extractedHeadings;
        }
        return prevHeadings;
      });
    }, 50); // 50ms debounce delay - adjust if needed
  }, []); // Dependency array is empty as setHeadings is stable

  // Cleanup timeout on unmount
  useEffect(() => {
    return () => {
      if (headingUpdateTimeoutRef.current !== null) {
        clearTimeout(headingUpdateTimeoutRef.current);
      }
    };
  }, []);

  // Clear headings when switching tabs away from markdown content
  const handleTabChange = (_: React.SyntheticEvent, newIndex: number) => {
    if (newIndex !== 0 && newIndex !== 1) {
      setHeadings([]); // Clear headings if not on Recommendation or Comparison tab
    }
    setTabIndex(newIndex);
  };

  // Toggle mobile drawer
  const toggleMobileToc = () => {
    setMobileTocOpen(!mobileTocOpen);
  };

    // Close mobile drawer (e.g., when a link is clicked)
  const closeMobileToc = () => {
    setMobileTocOpen(false);
  };


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
  // const isContentReady = !loadingInsurers && !insurerError && !loadingScenario && !scenarioError; // Removed unused variable
  const isLoading = loadingInsurers || loadingScenario;
  const hasError = insurerError || scenarioError;

  // Determine if TOC should be potentially visible (correct tab selected)
  const showTocArea = tabIndex === 0 || tabIndex === 1;

  return (
    <Box sx={{ width: '100%', bgcolor: 'background.paper', display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Header AppBar */}
      <AppBar position="static" color="default" elevation={1}>
        <Toolbar>
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            Aegis AI Report {/* Updated Title */}
          </Typography>
          {/* Mobile TOC Toggle Button REMOVED from AppBar */}
          <Button color="primary" variant="outlined" onClick={onSwitchCustomer} sx={{ ml: isMobile ? 1 : 2 }}> {/* Adjust margin for mobile */}
            Log out
          </Button>
        </Toolbar>
        {/* Tabs */}
        <Tabs
          value={tabIndex}
          onChange={handleTabChange} // Use updated handler
          indicatorColor="primary"
          textColor="primary"
          variant="scrollable" // Always use scrollable variant
          scrollButtons="auto"
          allowScrollButtonsMobile
          // centered={!isMobile} // Remove centered prop, not ideal with scrollable
        >
          {tabLabels.map((tab) => (
            <Tab key={tab.label} label={tab.label} icon={tab.icon} iconPosition="start" /> // Always show label
          ))}
        </Tabs>
      </AppBar>

      {/* Main Content Area - Using Box with Flexbox instead of Grid */}
      <Box sx={{ flexGrow: 1, p: isMobile ? 1 : 3, overflowY: 'auto', display: 'flex' }}>
          {/* Content Column (Box) */}
          <Box sx={{ flexGrow: 1, maxWidth: showTocArea && !isMobile && headings.length > 0 ? '75%' : '100%' }}> {/* Adjust width based on TOC visibility */}
            {tabIndex === 0 && (
                  <> {/* Wrap in Fragment */}
                    <MarkdownRenderer
                      filePath={recommendationPath}
                      animationMode="character"
                      onHeadingsExtracted={handleHeadingsExtracted} // Pass callback
                    />
                    <FeedbackButtons /> {/* Add FeedbackButtons here */}
                  </>
                )}
                {tabIndex === 1 && (
                  <Box>
                {loadingInsurers ? (
                  <CircularProgress size={24} />
                ) : insurerError ? (
                  <Typography color="error">{insurerError}</Typography>
                ) : (
                  // Wrap Dropdown and Mobile TOC Button in a Flex Box
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, gap: 1 }}>
                    <FormControl sx={{ minWidth: 240, flexGrow: 1 }} disabled={availableInsurers.length === 0}> {/* Allow dropdown to grow */}
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
                    {/* Conditionally render IconButton for mobile TOC toggle */}
                    {isMobile && tabIndex === 1 && headings.length > 0 && (
                      <IconButton
                        color="primary" // Use primary color to match other controls potentially
                        aria-label="open table of contents"
                        edge="end" // Keep edge alignment if desired, or remove
                        onClick={toggleMobileToc}
                        // sx={{ ml: 1 }} // Adjust styling as needed, maybe remove ml if gap is sufficient
                      >
                        <MenuIcon />
                      </IconButton>
                    )}
                   </Box>
                )}
                {policyComparisonPath ? (
                  <MarkdownRenderer
                    filePath={policyComparisonPath}
                    animationMode="paragraph"
                    onHeadingsExtracted={handleHeadingsExtracted} // Pass callback
                  />
                ) : !loadingInsurers && !insurerError ? (
                  <Typography>Select an insurer to view the comparison.</Typography>
                    ) : null}
                    <FeedbackButtons /> {/* Add FeedbackButtons here */}
                  </Box>
                )}
                {tabIndex === 2 && (
                  isLoading ? <CircularProgress size={24} /> :
                  hasError ? <Typography color="error">{scenarioError || 'Error loading data.'}</Typography> :
                  requirementsPath ? (
                    <> {/* Wrap in Fragment */}
                      <JsonPrettyViewer filePath={requirementsPath} dataPath="json_dict" />
                      <FeedbackButtons />
                    </>
                  ) : (
                    <Typography>Could not determine requirements file path.</Typography>
                  )
                )}
                {tabIndex === 3 && (
                  isLoading ? <CircularProgress size={24} /> :
                  hasError ? <Typography color="error">{scenarioError || 'Error loading data.'}</Typography> :
                  transcriptPath ? (
                    <> {/* Wrap in Fragment */}
                      <TranscriptViewer filePath={transcriptPath} />
                      <FeedbackButtons />
                    </>
                  ) : (
                    <Typography>Could not determine transcript file path.</Typography>
                  )
                )}
                {tabIndex === 4 && ( /* Add rendering for Feedback tab */
                  <FeedbackTabContent />
                )}
              </Box>

              {/* Desktop TOC Column (Box) */}
          {!isMobile && showTocArea && headings.length > 0 && (
            <Box sx={{
              width: '25%', // Give TOC a width
              pl: 2, // Add padding left
              position: 'sticky', // Make TOC sticky
              top: theme.spacing(2), // Adjust top spacing as needed
              height: 'calc(100vh - 120px)', // Adjust height
              overflowY: 'auto', // Allow TOC to scroll
            }}>
              <TableOfContents headings={headings} />
            </Box>
          )}
      </Box>

      {/* Mobile TOC Drawer */}
      <Drawer
        anchor="right"
        open={mobileTocOpen}
        onClose={closeMobileToc}
        ModalProps={{
          keepMounted: true, // Better open performance on mobile.
        }}
        sx={{
          display: { xs: 'block', md: 'none' }, // Only display Drawer on mobile
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 280 }, // Adjust drawer width
        }}
      >
        <TableOfContents headings={headings} onLinkClick={closeMobileToc} /> {/* Close drawer on link click */}
      </Drawer>
    </Box>
  );
};
