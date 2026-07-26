import clsx from "clsx";

export function Card({
  className,
  children,
}: {
  className?: string;
  children: React.ReactNode;
}) {
  return (
    <div
      className={clsx(
        "bg-ink-panel border border-ink-border rounded-md",
        className
      )}
    >
      {children}
    </div>
  );
}

export function SectionLabel({
  number,
  title,
}: {
  number: string;
  title: string;
}) {
  return (
    <div className="flex items-baseline gap-3 mb-4">
      <span className="font-mono text-xs text-gold tracking-widest">{number}</span>
      <h2 className="font-display text-lg text-paper tracking-tight">{title}</h2>
      <div className="memo-divider flex-1" />
    </div>
  );
}

export function Button({
  className,
  variant = "primary",
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "danger";
}) {
  const styles = {
    primary:
      "bg-gold text-ink hover:bg-gold-bright disabled:opacity-40 disabled:cursor-not-allowed",
    ghost:
      "bg-transparent text-paper-muted border border-ink-border hover:text-paper hover:border-paper-faint",
    danger:
      "bg-transparent text-signal-negative border border-signal-negative/40 hover:bg-signal-negative/10",
  };
  return (
    <button
      className={clsx(
        "px-4 py-2 text-sm font-medium rounded focus-ring transition-colors",
        styles[variant],
        className
      )}
      {...props}
    />
  );
}

export function Input({
  label,
  className,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & { label?: string }) {
  return (
    <label className="block">
      {label && (
        <span className="block text-xs uppercase tracking-wider text-paper-faint mb-1.5">
          {label}
        </span>
      )}
      <input
        className={clsx(
          "w-full bg-ink border border-ink-border rounded px-3 py-2 text-sm text-paper",
          "placeholder:text-paper-faint focus-ring focus:border-gold-dim outline-none",
          className
        )}
        {...props}
      />
    </label>
  );
}

export function Select({
  label,
  className,
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & { label?: string }) {
  return (
    <label className="block">
      {label && (
        <span className="block text-xs uppercase tracking-wider text-paper-faint mb-1.5">
          {label}
        </span>
      )}
      <select
        className={clsx(
          "w-full bg-ink border border-ink-border rounded px-3 py-2 text-sm text-paper",
          "focus-ring focus:border-gold-dim outline-none",
          className
        )}
        {...props}
      >
        {children}
      </select>
    </label>
  );
}

export function Tag({
  children,
  tone = "neutral",
}: {
  children: React.ReactNode;
  tone?: "neutral" | "positive" | "negative" | "gold";
}) {
  const styles = {
    neutral: "bg-ink-raised text-paper-muted border-ink-border",
    positive: "bg-signal-positive/10 text-signal-positive border-signal-positive/30",
    negative: "bg-signal-negative/10 text-signal-negative border-signal-negative/30",
    gold: "bg-gold/10 text-gold border-gold/30",
  };
  return (
    <span
      className={clsx(
        "inline-block px-2 py-0.5 text-xs rounded border font-mono",
        styles[tone]
      )}
    >
      {children}
    </span>
  );
}

export function Stat({
  label,
  value,
  tone = "neutral",
  suffix,
}: {
  label: string;
  value: string | number;
  tone?: "neutral" | "positive" | "negative";
  suffix?: string;
}) {
  const toneColor = {
    neutral: "text-paper",
    positive: "text-signal-positive",
    negative: "text-signal-negative",
  };
  return (
    <div className="border border-ink-border rounded p-4 bg-ink">
      <div className="text-xs uppercase tracking-wider text-paper-faint mb-1.5">
        {label}
      </div>
      <div className={clsx("font-mono text-2xl tabular-nums", toneColor[tone])}>
        {value}
        {suffix && <span className="text-sm text-paper-muted ml-1">{suffix}</span>}
      </div>
    </div>
  );
}
