interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  data: T[];
}
