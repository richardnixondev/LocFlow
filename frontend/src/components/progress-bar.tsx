interface ProgressBarProps {
  percent: number;
  label?: string;
  size?: "sm" | "md";
}

export default function ProgressBar({
  percent,
  label,
  size = "md",
}: ProgressBarProps) {
  const height = size === "sm" ? "h-2" : "h-3";
  const color =
    percent >= 100
      ? "bg-green-500"
      : percent >= 50
        ? "bg-blue-500"
        : "bg-amber-500";

  return (
    <div className="w-full">
      {label && (
        <div className="flex justify-between text-sm mb-1">
          <span className="text-gray-600">{label}</span>
          <span className="font-medium">{percent}%</span>
        </div>
      )}
      <div className={`w-full ${height} bg-gray-200 rounded-full overflow-hidden`}>
        <div
          className={`${height} ${color} rounded-full transition-all duration-500`}
          style={{ width: `${Math.min(percent, 100)}%` }}
        />
      </div>
    </div>
  );
}
