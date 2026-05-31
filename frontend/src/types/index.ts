export type Agent = {
  id: string;
  name: string;
  role: string;
  system_prompt: string;
  model: string;
  tools: string[];
  channels: string[];
  schedules: Record<string, unknown>;
  memory: Record<string, unknown>;
  limits: Record<string, unknown>;
  skills: string[];
  interaction_rules: string[];
  guardrails: string[];
  runtime_node_binding: string | null;
  created_at: string;
  updated_at: string;
};

export type WorkflowTemplate = {
  id: string;
  key: string;
  name: string;
  description: string;
  category: string;
  graph: WorkflowGraph;
  default_input: string;
  is_builtin: boolean;
  created_at: string;
  updated_at: string;
};

export type WorkflowGraph = {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
};

export type WorkflowNode = {
  id: string;
  type: string;
  label: string;
  x: number;
  y: number;
};

export type WorkflowEdge = {
  source: string;
  target: string;
  label: string;
};

export type WorkflowRun = {
  id: string;
  template_key: string;
  status: "queued" | "running" | "completed" | "failed" | "awaiting_approval";
  channel: string;
  input_message: string;
  final_response: string | null;
  token_count: number;
  estimated_cost_usd: number;
  confidence: number | null;
  source_metadata: Record<string, unknown>;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  messages?: AgentMessage[];
  events?: RunEvent[];
  tool_calls?: ToolExecution[];
};

export type AgentMessage = {
  id: string;
  run_id: string;
  sender: string;
  recipient: string;
  channel: string;
  content: string;
  payload: Record<string, unknown>;
  created_at: string;
};

export type RunEvent = {
  id: string;
  run_id: string;
  event_type: string;
  title: string;
  body: string;
  node_id: string | null;
  payload: Record<string, unknown>;
  token_count: number;
  cost_usd: number;
  created_at: string;
};

export type ToolExecution = {
  id: string;
  run_id: string;
  tool_name: string;
  status: string;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  duration_ms: number;
  created_at: string;
};

export type Metrics = {
  total_runs: number;
  completed_runs: number;
  failed_runs: number;
  active_agents: number;
  total_messages: number;
  total_tokens: number;
  estimated_cost_usd: number;
};