/**
 * Task History Component
 *
 * Displays historical tasks with search, filtering, and sorting capabilities.
 * Features:
 * - Full-text search across task descriptions
 * - Date range filtering
 * - Status filtering
 * - Sortable columns
 * - Pagination
 */
// @ts-nocheck
import { useState } from 'react';
import { Search, Filter, ChevronDown, ChevronUp, Calendar } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { taskApi } from '../services/api';
import type { Task } from '../types';

interface TaskHistoryFilters {
  search: string;
  status: string;
  dateFrom: string;
  dateTo: string;
  costMin: string;
  costMax: string;
  durationMin: string;
  durationMax: string;
  sortBy: string;
  sortOrder: 'asc' | 'desc';
}

export function TaskHistory() {
  const [page, setPage] = useState(1);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState<TaskHistoryFilters>({
    search: '',
    status: '',
    dateFrom: '',
    dateTo: '',
    costMin: '',
    costMax: '',
    durationMin: '',
    durationMax: '',
    sortBy: 'created_at',
    sortOrder: 'desc'
  });

  // Fetch tasks with filters
  const { data, isLoading, error } = useQuery({
    queryKey: ['taskHistory', page, filters],
    queryFn: () => {
      const params = new URLSearchParams();
      params.append('page', page.toString());
      params.append('page_size', '20');

      if (filters.search) params.append('search', filters.search);
      if (filters.status) params.append('status', filters.status);
      if (filters.dateFrom) params.append('date_from', filters.dateFrom);
      if (filters.dateTo) params.append('date_to', filters.dateTo);
      if (filters.costMin) params.append('cost_min', filters.costMin);
      if (filters.costMax) params.append('cost_max', filters.costMax);
      if (filters.durationMin) params.append('duration_min', filters.durationMin);
      if (filters.durationMax) params.append('duration_max', filters.durationMax);
      params.append('sort_by', filters.sortBy);
      params.append('sort_order', filters.sortOrder);

      return taskApi.list(params);
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  const handleFilterChange = (key: keyof TaskHistoryFilters, value: string) => {
    setFilters((prev: TaskHistoryFilters) => ({ ...prev, [key]: value }));
    setPage(1); // Reset to first page when filters change
  };

  const handleSort = (field: string) => {
    if (filters.sortBy === field) {
      // Toggle sort order
      setFilters((prev: TaskHistoryFilters) => ({
        ...prev,
        sortOrder: prev.sortOrder === 'asc' ? 'desc' : 'asc'
      }));
    } else {
      // Change sort field
      setFilters((prev: TaskHistoryFilters) => ({
        ...prev,
        sortBy: field,
        sortOrder: 'desc'
      }));
    }
  };

  const clearFilters = () => {
    setFilters({
      search: '',
      status: '',
      dateFrom: '',
      dateTo: '',
      costMin: '',
      costMax: '',
      durationMin: '',
      durationMax: '',
      sortBy: 'created_at',
      sortOrder: 'desc'
    });
    setPage(1);
  };

  const formatDate = (dateStr: string): string => {
    const date = new Date(dateStr);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  const formatCost = (cents: number | null | undefined): string => {
    if (cents === null || cents === undefined) return 'N/A';
    return `$${(cents / 100).toFixed(2)}`;
  };

  const formatDuration = (seconds: number | null | undefined): string => {
    if (seconds === null || seconds === undefined) return 'N/A';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes}m ${remainingSeconds}s`;
  };

  const getStatusBadge = (status: string) => {
    const statusColors: Record<string, string> = {
      completed: 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200',
      failed: 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200',
      in_progress: 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200',
      pending: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-200'
    };

    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusColors[status] || statusColors.pending}`}>
        {status.replace('_', ' ').toUpperCase()}
      </span>
    );
  };

  const SortIcon = ({ field }: { field: string }) => {
    if (filters.sortBy !== field) return null;
    return filters.sortOrder === 'asc' ?
      <ChevronUp className="inline h-4 w-4" /> :
      <ChevronDown className="inline h-4 w-4" />;
  };

  const totalPages = data ? Math.ceil(data.total / 20) : 0;

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Task History</h2>
          <p className="text-sm text-muted-foreground">
            {data?.total || 0} tasks total
          </p>
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          <Filter className="h-4 w-4" />
          {showFilters ? 'Hide Filters' : 'Show Filters'}
        </button>
      </div>

      {/* Filters Panel */}
      {showFilters && (
        <div className="bg-muted/50 p-4 rounded-lg space-y-4">
          {/* Search */}
          <div>
            <label className="text-sm font-medium block mb-2">Search</label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                placeholder="Search task descriptions..."
                className="w-full pl-10 pr-4 py-2 bg-background border border-border rounded-md"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Status Filter */}
            <div>
              <label className="text-sm font-medium block mb-2">Status</label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-md"
              >
                <option value="">All Statuses</option>
                <option value="completed">Completed</option>
                <option value="failed">Failed</option>
                <option value="in_progress">In Progress</option>
                <option value="pending">Pending</option>
              </select>
            </div>

            {/* Date From */}
            <div>
              <label className="text-sm font-medium block mb-2">Date From</label>
              <input
                type="date"
                value={filters.dateFrom}
                onChange={(e) => handleFilterChange('dateFrom', e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-md"
              />
            </div>

            {/* Date To */}
            <div>
              <label className="text-sm font-medium block mb-2">Date To</label>
              <input
                type="date"
                value={filters.dateTo}
                onChange={(e) => handleFilterChange('dateTo', e.target.value)}
                className="w-full px-3 py-2 bg-background border border-border rounded-md"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* Cost Min (in cents) */}
            <div>
              <label className="text-sm font-medium block mb-2">Min Cost (cents)</label>
              <input
                type="number"
                value={filters.costMin}
                onChange={(e) => handleFilterChange('costMin', e.target.value)}
                placeholder="0"
                min="0"
                className="w-full px-3 py-2 bg-background border border-border rounded-md"
              />
            </div>

            {/* Cost Max (in cents) */}
            <div>
              <label className="text-sm font-medium block mb-2">Max Cost (cents)</label>
              <input
                type="number"
                value={filters.costMax}
                onChange={(e) => handleFilterChange('costMax', e.target.value)}
                placeholder="No limit"
                min="0"
                className="w-full px-3 py-2 bg-background border border-border rounded-md"
              />
            </div>

            {/* Duration Min (in seconds) */}
            <div>
              <label className="text-sm font-medium block mb-2">Min Duration (sec)</label>
              <input
                type="number"
                value={filters.durationMin}
                onChange={(e) => handleFilterChange('durationMin', e.target.value)}
                placeholder="0"
                min="0"
                className="w-full px-3 py-2 bg-background border border-border rounded-md"
              />
            </div>

            {/* Duration Max (in seconds) */}
            <div>
              <label className="text-sm font-medium block mb-2">Max Duration (sec)</label>
              <input
                type="number"
                value={filters.durationMax}
                onChange={(e) => handleFilterChange('durationMax', e.target.value)}
                placeholder="No limit"
                min="0"
                className="w-full px-3 py-2 bg-background border border-border rounded-md"
              />
            </div>
          </div>

          {/* Filter Actions */}
          <div className="flex justify-end gap-2">
            <button
              onClick={clearFilters}
              className="px-4 py-2 text-sm bg-background border border-border rounded-md hover:bg-muted"
            >
              Clear Filters
            </button>
          </div>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-primary border-r-transparent"></div>
          <p className="mt-4 text-muted-foreground">Loading tasks...</p>
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="bg-destructive/10 border border-destructive text-destructive px-4 py-3 rounded-lg">
          <p className="font-medium">Error loading tasks</p>
          <p className="text-sm">{error instanceof Error ? error.message : 'Unknown error'}</p>
        </div>
      )}

      {/* Tasks Table */}
      {!isLoading && !error && data && (
        <>
          <div className="bg-background border border-border rounded-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-muted">
                  <tr>
                    <th
                      className="px-4 py-3 text-left text-sm font-medium cursor-pointer hover:bg-muted/80"
                      onClick={() => handleSort('created_at')}
                    >
                      Date <SortIcon field="created_at" />
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium">
                      Description
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium">
                      Status
                    </th>
                    <th className="px-4 py-3 text-left text-sm font-medium">
                      Type
                    </th>
                    <th className="px-4 py-3 text-center text-sm font-medium">
                      Agents
                    </th>
                    <th
                      className="px-4 py-3 text-right text-sm font-medium cursor-pointer hover:bg-muted/80"
                      onClick={() => handleSort('total_cost')}
                    >
                      Cost <SortIcon field="total_cost" />
                    </th>
                    <th
                      className="px-4 py-3 text-right text-sm font-medium cursor-pointer hover:bg-muted/80"
                      onClick={() => handleSort('duration_seconds')}
                    >
                      Duration <SortIcon field="duration_seconds" />
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {data.tasks.map((task: Task) => (
                    <tr key={task.id} className="hover:bg-muted/50">
                      <td className="px-4 py-3 text-sm whitespace-nowrap">
                        {formatDate(task.created_at)}
                      </td>
                      <td className="px-4 py-3 text-sm max-w-md truncate">
                        {task.description}
                      </td>
                      <td className="px-4 py-3 text-sm">
                        {getStatusBadge(task.status)}
                      </td>
                      <td className="px-4 py-3 text-sm capitalize">
                        {task.task_type?.replace(/_/g, ' ') || 'N/A'}
                      </td>
                      <td className="px-4 py-3 text-sm text-center">
                        {task.workflow?.length || 0}
                      </td>
                      <td className="px-4 py-3 text-sm text-right font-mono">
                        {formatCost(task.total_cost)}
                      </td>
                      <td className="px-4 py-3 text-sm text-right font-mono">
                        {formatDuration(task.duration_seconds)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Page {page} of {totalPages}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p: number) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 text-sm bg-background border border-border rounded-md hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Previous
                </button>
                <button
                  onClick={() => setPage((p: number) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 text-sm bg-background border border-border rounded-md hover:bg-muted disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Next
                </button>
              </div>
            </div>
          )}

          {/* Empty State */}
          {data.tasks.length === 0 && (
            <div className="text-center py-12">
              <Calendar className="mx-auto h-12 w-12 text-muted-foreground/50" />
              <p className="mt-4 text-lg font-medium">No tasks found</p>
              <p className="text-sm text-muted-foreground">
                Try adjusting your filters or search terms
              </p>
            </div>
          )}
        </>
      )}
    </div>
  );
}
