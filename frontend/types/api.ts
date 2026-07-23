export interface ApiErrorBody {
  detail?: string | { msg?: string; type?: string }[];
  message?: string;
}

export interface ApiFailure {
  status: number;
  message: string;
  retryable: boolean;
}

export interface PaginationState {
  cursor?: string;
  hasMore: boolean;
}
