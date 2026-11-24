interface UloLogoProps {
  size?: number;
}

export default function UloLogo({ size = 54 }: UloLogoProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="Urmia Lake Scientific Observatory Logo"
      style={{ flexShrink: 0 }}
    >
      <defs>
        <linearGradient id="uloOrbGrad" x1="6" y1="6" x2="58" y2="58" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#00ACC1" />
          <stop offset="55%" stopColor="#1565C0" />
          <stop offset="100%" stopColor="#0B1F3A" />
        </linearGradient>
        <linearGradient id="uloLakeSil" x1="20" y1="14" x2="42" y2="50" gradientUnits="userSpaceOnUse">
          <stop offset="0%" stopColor="#E0F7FA" />
          <stop offset="100%" stopColor="#4DD0E1" />
        </linearGradient>
      </defs>

      {/* Outer Earth Observation Ring */}
      <circle cx="32" cy="32" r="29" fill="url(#uloOrbGrad)" stroke="rgba(255,255,255,0.45)" strokeWidth="1.5" />
      <circle cx="32" cy="32" r="23" stroke="rgba(248,250,252,0.22)" strokeWidth="1" strokeDasharray="3 3" />

      {/* Satellite Orbit Arc */}
      <ellipse
        cx="32"
        cy="32"
        rx="26"
        ry="11"
        transform="rotate(-28 32 32)"
        stroke="#D4B483"
        strokeWidth="1.35"
        strokeOpacity="0.85"
      />

      {/* Stylized Lake Urmia North-South Basin Silhouette */}
      <path
        d="M27.5 14.5C31.5 14.2 36.2 16.8 37.4 21.2C38.3 24.5 35.8 27.6 36.6 30.8C37.6 34.8 41.2 38.2 39.8 43.2C38.6 47.4 33.8 50.2 29.2 49.4C25.2 48.7 23.4 45.1 24.2 41.2C24.9 37.9 27.2 35.8 26.8 32.4C26.3 28.5 22.8 25.8 23.2 21.2C23.5 17.4 25.1 14.8 27.5 14.5Z"
        fill="url(#uloLakeSil)"
        fillOpacity="0.92"
      />

      {/* Causeway / Wave Horizon Lines */}
      <path
        d="M18 35.5C22.5 33.8 27.2 37.2 32 35.5C36.8 33.8 41.5 37.2 46 35.5"
        stroke="#0B1F3A"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
      <path
        d="M20 40.2C24 38.8 28 41.6 32 40.2C36 38.8 40 41.6 44 40.2"
        stroke="#F8FAFC"
        strokeWidth="1.3"
        strokeLinecap="round"
        strokeOpacity="0.85"
      />

      {/* Satellite Sensor Node */}
      <g transform="translate(47, 14) rotate(-28)">
        <rect x="-3" y="-2.2" width="6" height="4.4" rx="1" fill="#F8FAFC" />
        <rect x="-8.5" y="-1.4" width="4.5" height="2.8" rx="0.5" fill="#D4B483" />
        <rect x="4" y="-1.4" width="4.5" height="2.8" rx="0.5" fill="#D4B483" />
      </g>
    </svg>
  );
}