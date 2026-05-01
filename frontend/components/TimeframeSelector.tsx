const ALL_TIMEFRAMES = ["15m", "1d", "7d", "1month", "1y"];

type TimeframeSelectorProps = {
  selected: string[];
  onChange: (selected: string[]) => void;
};

export default function TimeframeSelector({ selected, onChange }: TimeframeSelectorProps) {
  const toggle = (timeframe: string) => {
    if (selected.includes(timeframe)) {
      onChange(selected.filter((t) => t !== timeframe));
    } else {
      onChange([...selected, timeframe]);
    }
  };

  return (
    <div className="timeframe-inline">
      <span className="timeframe-label">Horizons:</span>
      {ALL_TIMEFRAMES.map((timeframe) => {
        const isSelected = selected.includes(timeframe);
        return (
          <button
            key={timeframe}
            type="button"
            className={`timeframe-chip ${isSelected ? "timeframe-chip-active" : ""}`}
            onClick={() => toggle(timeframe)}
            aria-pressed={isSelected}
          >
            {timeframe}
          </button>
        );
      })}
    </div>
  );
}
