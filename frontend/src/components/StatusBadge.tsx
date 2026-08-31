import { STATUS_COLORS, STATUS_LABELS } from '../utils';

export function StatusBadge({ status }: { status: string }) {
  return (
    <span className={`inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-semibold border ${STATUS_COLORS[status] || STATUS_COLORS.unknown}`}>
      {STATUS_LABELS[status] || status}
    </span>
  );
}
