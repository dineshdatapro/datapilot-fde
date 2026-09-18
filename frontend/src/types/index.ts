export type ColumnProfile = {
  name: string;
  pandas_dtype: string;
  semantic_type: string;
  missing_count: number;
  unique_count: number;
  sample_values: unknown[];
};

export type UploadedFile = {
  file_id: string;
  filename: string;
  file_type: string;
  row_count: number;
  column_count: number;
  columns: ColumnProfile[];
};

export type Relationship = {
  left_file: string;
  left_column: string;
  right_file: string;
  right_column: string;
  confidence: string;
  overlap_ratio: number;
  reason: string;
};

export type SessionPayload = {
  session_id: string;
  files: UploadedFile[];
  overview: {
    file_count: number;
    total_rows: number;
    total_columns: number;
    relationships: Relationship[];
  };
};

export type Visualization = {
  type: "kpi" | "bar" | "line" | "grouped_bar" | "horizontal_bar" | "pie" | "table" | "none";
  title: string;
  data: Record<string, unknown>[];
  x_key?: string;
  y_key?: string;
  value_format?: string;
};

export type QueryResponse = {
  question: string;
  answer: string;
  verified: boolean;
  files_used: string[];
  rows_analyzed: number;
  plan: Record<string, unknown>;
  result: Record<string, unknown>;
  visualization: Visualization;
  analysis: {
    files_used?: string[];
    rows_analyzed?: number;
    operation?: string;
    grouping?: string;
    filters?: string;
    join?: Record<string, string> | null;
    trust?: string;
  };
  error?: string | null;
};
