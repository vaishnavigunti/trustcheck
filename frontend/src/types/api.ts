// API types.

export interface ApiError {
  error: {
    type: string;
    message: string;
  };
}

export interface ApiResponse<T> {
  data?: T;
  error?: ApiError;
}
