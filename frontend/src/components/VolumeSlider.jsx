import { useRef } from 'react';

export default function VolumeSlider({ value, onChange, label = 'Volume', min = 0, max = 1, step = 0.01 }) {
  const debounceRef = useRef();

  const handleChange = (e) => {
    const v = Number(e.target.value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      onChange(v);
    }, 300);
  };

  return (
    <div style={{ marginTop: 16, textAlign: 'center' }}>
      <label htmlFor="volume-slider">{label}: {(value * 100).toFixed(0)}%</label>
      <input
        id="volume-slider"
        type="range"
        min={min}
        max={max}
        step={step}
        defaultValue={value}
        onChange={handleChange}
        style={{ width: '100%' }}
      />
    </div>
  );
} 