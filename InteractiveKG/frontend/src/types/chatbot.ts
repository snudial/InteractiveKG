

export enum TestScenario {
  STAGE_1 = "stage_1",
  STAGE_2 = "stage_2"
}

export enum TestPhase {
  
  CASE1_INTRO = "case1_intro",
  CASE1_LLM_RESPONSE = "case1_llm_response",
  CASE1_EXPLORE_GRAPH = "case1_explore_graph",
  CASE1_IDENTIFY_ERRORS = "case1_identify_errors",
  CASE1_EDIT_CORRECT = "case1_edit_correct",
  CASE1_REQUERY_COMPARE = "case1_requery_compare",

  
  CASE2_INTRO = "case2_intro",
  CASE2_LLM_RESPONSE = "case2_llm_response",
  CASE2_EXPLORE_GRAPH = "case2_explore_graph",
  CASE2_IDENTIFY_ERRORS = "case2_identify_errors",
  CASE2_EDIT_CORRECT = "case2_edit_correct",
  CASE2_REQUERY_COMPARE = "case2_requery_compare"
}

export enum ChatbotRole {
  SYSTEM = "system",
  ASSISTANT = "assistant",
  USER = "user"
}

export interface ChatMessage {
  role: ChatbotRole;
  content: string;
  timestamp?: string;
  metadata?: Record<string, any>;
}

export interface ChatbotState {
  session_id: string;
  current_scenario?: TestScenario;
  current_phase: TestPhase;
  user_role: string;
  messages: ChatMessage[];
  scenario_data_loaded: boolean;
  case1_completed: boolean;
  case2_completed: boolean;
  error_dataset_loaded?: string | null;
  metadata: Record<string, any>;
}

export interface ChatbotRequest {
  session_id: string;
  message: string;
  action?: string;
}



export interface UIInstructions {
  highlight_panel?: string;
  highlight_tab?: string;
  show_tooltip?: string;
  focus_element?: string;
}

export interface DataSourceSelectionButton {
  id: string;
  label: string;
  domain: string;
  file: string;
  title: string;
  description: string;
  variant: 'primary' | 'secondary' | 'success' | 'warning';
}

export interface ChatbotResponse {
  session_id: string;
  message: string;
  current_phase: TestPhase;
  current_scenario?: TestScenario;
  ui_instructions: UIInstructions;
  advance_button?: {
    label: string;
    description: string;
    target_phase: string;
    variant: 'primary' | 'secondary' | 'success' | 'warning';
  };
  data_source_selection_buttons?: DataSourceSelectionButton[];
  success: boolean;
  error?: string;
}

export interface ScenarioInfo {
  scenario_name: string;
  description: string;
  user_role: string;
  target_question: string;
  expected_issue: string;
}

export interface SessionInfo {
  session_id: string;
  current_phase: TestPhase;
  current_scenario?: TestScenario;
  progress_percentage: number;
  phase_description: string;
  messages_count: number;
  case1_completed: boolean;
  case2_completed: boolean;
  advance_button?: any;
  data_source_selection_buttons?: any[];
}

export interface ScenarioLoadRequest {
  session_id: string;
  scenario: TestScenario;
}

export interface ScenarioLoadResponse {
  session_id: string;
  scenario: TestScenario;
  data_loaded: boolean;
  nodes_count: number;
  relationships_count: number;
  success: boolean;
  error?: string;
}

export interface IntegrationAction {
  session_id: string;
  action_type: 'highlight_nodes' | 'open_property_panel' | 'trigger_search' | 'load_data';
  parameters: Record<string, any>;
}

export interface ChatbotPanelProps {
  onDataUpdate?: (sampleData?: any) => void;
  onHighlightNodes?: (nodeIds: string[]) => void;
  onOpenPropertyPanel?: (nodeId: string) => void;
  onTriggerKGOTSearch?: (query: string, tab: 'solve' | 'retrieve') => void;
  currentGraphData?: any;
}
