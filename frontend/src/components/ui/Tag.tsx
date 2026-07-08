import type { ReactNode } from "react";
import { CheckCircle2, AlertTriangle, XCircle, Info } from "lucide-react";

export type TagTone = "ok" | "warn" | "danger" | "info";

const ICONS: Record<TagTone, typeof Info> = {
  ok: CheckCircle2,
  warn: AlertTriangle,
  danger: XCircle,
  info: Info,
};

export function Tag({ tone, children, title }: { tone: TagTone; children: ReactNode; title?: string }) {
  const Icon = ICONS[tone];
  return (
    <span className={`tag ${tone}`} title={title}>
      <Icon size={12} aria-hidden />
      {children}
    </span>
  );
}

/** Verification status → tone, paired with an icon and label (never color alone). */
export function VerificationTag({ status }: { status?: string }) {
  if (!status) return <span className="muted">—</span>;
  const tone: TagTone = status === "VERIFIED" ? "ok" : "warn";
  return (
    <Tag tone={tone} title="ResStock/ComStock enumeration verification status">
      {status}
    </Tag>
  );
}

export function WeatherQcTag({ status }: { status?: string }) {
  if (!status) return <span className="muted">—</span>;
  const tone: TagTone = status === "COMPLETE" ? "ok" : "warn";
  return (
    <Tag tone={tone} title="Hourly weather QC: ≥90% of the year's temperature + humidity observations">
      {status}
    </Tag>
  );
}
