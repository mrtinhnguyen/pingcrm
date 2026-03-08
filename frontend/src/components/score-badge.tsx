import { cn } from "@/lib/utils";

interface ScoreBadgeProps {
  score: number;
  className?: string;
}

function getScoreVariant(score: number): {
  label: string;
  dotClass: string;
  textClass: string;
} {
  if (score >= 8) {
    return {
      label: "Strong",
      dotClass: "bg-emerald-500",
      textClass: "text-emerald-700",
    };
  }
  if (score >= 4) {
    return {
      label: "Active",
      dotClass: "bg-amber-400",
      textClass: "text-amber-700",
    };
  }
  return {
    label: "Dormant",
    dotClass: "bg-red-400",
    textClass: "text-red-600",
  };
}

export function ScoreBadge({ score, className }: ScoreBadgeProps) {
  const { label, dotClass, textClass } = getScoreVariant(score);

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 text-sm font-medium",
        textClass,
        className
      )}
      title={`Relationship score: ${score}/10`}
    >
      <span className={cn("w-2 h-2 rounded-full flex-shrink-0", dotClass)} />
      {label} <span className="font-mono-data">({score})</span>
    </span>
  );
}
