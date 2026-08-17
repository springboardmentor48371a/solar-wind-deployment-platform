import React from 'react';

export const RenewableBackground: React.FC = () => {
  return (
    <div className="fixed inset-0 overflow-hidden pointer-events-none z-0 bg-slate-950">
      {/* 1. Atmospheric Deep Navy & Twilight Gradient Canvas */}
      <svg
        className="w-full h-full object-cover"
        viewBox="0 0 1440 900"
        preserveAspectRatio="xMidYMax slice"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <defs>
          {/* Sky Gradient */}
          <linearGradient id="skyGrad" x1="50%" y1="0%" x2="50%" y2="100%">
            <stop offset="0%" stopColor="#080e1e" />
            <stop offset="60%" stopColor="#0f172a" />
            <stop offset="100%" stopColor="#1e293b" />
          </linearGradient>

          {/* Warm Sun Radial Glow */}
          <radialGradient id="sunGlow" cx="200" cy="180" r="250" fx="200" fy="180" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.25" />
            <stop offset="40%" stopColor="#d97706" stopOpacity="0.08" />
            <stop offset="100%" stopColor="#0f172a" stopOpacity="0" />
          </radialGradient>

          {/* Sun Core */}
          <radialGradient id="sunCore" cx="200" cy="180" r="40" fx="200" fy="180" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#fffbeb" />
            <stop offset="30%" stopColor="#fef08a" />
            <stop offset="70%" stopColor="#f59e0b" stopOpacity="0.8" />
            <stop offset="100%" stopColor="#d97706" stopOpacity="0" />
          </radialGradient>

          {/* Cloud Gradient */}
          <linearGradient id="cloudGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#334155" stopOpacity="0.15" />
            <stop offset="100%" stopColor="#1e293b" stopOpacity="0.02" />
          </linearGradient>

          {/* Solar Panel Specular Clip Paths */}
          <clipPath id="panelClip1">
            <polygon points="100,800 220,740 320,775 190,845" />
          </clipPath>
          <clipPath id="panelClip2">
            <polygon points="220,830 315,790 410,820 305,870" />
          </clipPath>
          <clipPath id="panelClip3">
            <polygon points="340,855 420,825 500,850 410,890" />
          </clipPath>
        </defs>

        {/* 2. BASE SKY BACKGROUND */}
        <rect width="1440" height="900" fill="url(#skyGrad)" />

        {/* 3. PULSING SUN AND HORIZON SOLAR ACCENT GLOW */}
        <circle cx="200" cy="180" r="250" fill="url(#sunGlow)" className="animate-sun-pulse" />
        <circle cx="200" cy="180" r="50" fill="url(#sunCore)" className="animate-sun-pulse" />

        {/* 4. DRifting SVG CLOUDS */}
        <g className="opacity-40 hidden md:block">
          {/* Cloud 1 */}
          <path
            className="animate-cloud-drift-1"
            d="M 50 120 Q 90 90, 140 100 T 240 120 T 320 110 T 380 130 L 380 180 L 50 180 Z"
            fill="url(#cloudGrad)"
          />
          {/* Cloud 2 */}
          <path
            className="animate-cloud-drift-2"
            d="M 800 160 Q 850 130, 910 140 T 1030 160 T 1120 150 T 1200 175 L 1200 220 L 800 220 Z"
            fill="url(#cloudGrad)"
          />
          {/* Cloud 3 */}
          <path
            className="animate-cloud-drift-3"
            d="M 300 80 Q 330 60, 370 70 T 450 80 T 520 75 T 580 90 L 580 120 L 300 120 Z"
            fill="url(#cloudGrad)"
          />
        </g>

        {/* 5. HILLS / MOUNTAINS LAYER */}
        {/* Back Hill */}
        <path d="M0 720 Q 350 620, 700 700 T 1440 680 L 1440 900 L 0 900 Z" fill="#090f1d" opacity="0.9" />
        {/* Mid Hill */}
        <path d="M0 780 Q 400 740, 800 810 T 1440 760 L 1440 900 L 0 900 Z" fill="#0d1527" opacity="0.95" />
        {/* Front Ground (Hides bases cleanly) */}
        <path d="M0 840 Q 500 820, 1000 860 T 1440 850 L 1440 900 L 0 900 Z" fill="#111a2e" />

        {/* 6. ISOMETRIC SOLAR PANEL GRID ARRAY (hidden on mobile) */}
        <g className="hidden sm:block">
          {/* Grid Panel 1 */}
          <polygon points="100,800 220,740 320,775 190,845" fill="#1e293b" stroke="#334155" strokeWidth="1.5" />
          <line x1="160" y1="770" x2="255" y2="810" stroke="#475569" strokeWidth="1" />
          <line x1="220" y1="740" x2="190" y2="845" stroke="#475569" strokeWidth="1" />
          {/* Reflection Glint 1 */}
          <g clipPath="url(#panelClip1)">
            <line x1="0" y1="700" x2="400" y2="900" stroke="#fbbf24" strokeWidth="16" opacity="0.12" className="animate-solar-glint" />
          </g>

          {/* Grid Panel 2 */}
          <polygon points="220,830 315,790 410,820 305,870" fill="#1e293b" stroke="#334155" strokeWidth="1.5" />
          <line x1="267" y1="810" x2="357" y2="845" stroke="#475569" strokeWidth="1" />
          <line x1="315" y1="790" x2="305" y2="870" stroke="#475569" strokeWidth="1" />
          {/* Reflection Glint 2 */}
          <g clipPath="url(#panelClip2)">
            <line x1="100" y1="750" x2="500" y2="950" stroke="#fbbf24" strokeWidth="16" opacity="0.12" className="animate-solar-glint" style={{ animationDelay: '1.5s' }} />
          </g>

          {/* Grid Panel 3 */}
          <polygon points="340,855 420,825 500,850 410,890" fill="#1e293b" stroke="#334155" strokeWidth="1.5" />
          <line x1="380" y1="840" x2="455" y2="870" stroke="#475569" strokeWidth="1" />
          <line x1="420" y1="825" x2="410" y2="890" stroke="#475569" strokeWidth="1" />
          {/* Reflection Glint 3 */}
          <g clipPath="url(#panelClip3)">
            <line x1="200" y1="780" x2="600" y2="980" stroke="#fbbf24" strokeWidth="16" opacity="0.12" className="animate-solar-glint" style={{ animationDelay: '3s' }} />
          </g>
        </g>

        {/* 7. WIND TURBINES (with multi-tier depth) */}
        {/* Turbine 1 (Foreground, Left/Center-Right on Desktop, hidden on mobile) */}
        <g className="hidden sm:block">
          {/* Tower */}
          <path d="M 1146 860 L 1148.5 550 L 1151.5 550 L 1154 860 Z" fill="#475569" />
          <path d="M 1148 860 L 1149.5 550 L 1150.5 550 L 1152 860 Z" fill="#94a3b8" /> {/* Highlight */}
          <circle cx="1150" cy="550" r="7" fill="#cbd5e1" />
          {/* Blades group spinning centered on (1150, 550) */}
          <g style={{ transformOrigin: '1150px 550px' }} className="animate-spin-slow">
            {/* Blade A */}
            <path d="M 1148.5 550 C 1147 430, 1147.5 380, 1150 380 C 1152.5 380, 1153 430, 1151.5 550 Z" fill="#cbd5e1" />
            {/* Blade B */}
            <g transform="rotate(120, 1150, 550)">
              <path d="M 1148.5 550 C 1147 430, 1147.5 380, 1150 380 C 1152.5 380, 1153 430, 1151.5 550 Z" fill="#cbd5e1" />
            </g>
            {/* Blade C */}
            <g transform="rotate(240, 1150, 550)">
              <path d="M 1148.5 550 C 1147 430, 1147.5 380, 1150 380 C 1152.5 380, 1153 430, 1151.5 550 Z" fill="#cbd5e1" />
            </g>
          </g>
        </g>

        {/* Turbine 2 (Midground, Center-Right, hidden on mobile) */}
        <g className="hidden md:block">
          {/* Tower */}
          <path d="M 947.5 820 L 949 610 L 951 610 L 952.5 820 Z" fill="#334155" />
          <path d="M 948.5 820 L 949.5 610 L 950.5 610 L 951.5 820 Z" fill="#64748b" /> {/* Highlight */}
          <circle cx="950" cy="610" r="5" fill="#94a3b8" />
          {/* Blades group spinning centered on (950, 610) */}
          <g style={{ transformOrigin: '950px 610px' }} className="animate-spin-medium">
            {/* Blade A */}
            <path d="M 949 610 C 947.5 520, 948 480, 950 480 C 952 480, 952.5 520, 951 610 Z" fill="#94a3b8" />
            {/* Blade B */}
            <g transform="rotate(120, 950, 610)">
              <path d="M 949 610 C 947.5 520, 948 480, 950 480 C 952 480, 952.5 520, 951 610 Z" fill="#94a3b8" />
            </g>
            {/* Blade C */}
            <g transform="rotate(240, 950, 610)">
              <path d="M 949 610 C 947.5 520, 948 480, 950 480 C 952 480, 952.5 520, 951 610 Z" fill="#94a3b8" />
            </g>
          </g>
        </g>

        {/* Turbine 3 (Far background, Left, hidden on tablet & mobile) */}
        <g className="hidden lg:block">
          {/* Tower */}
          <path d="M 718.5 780 L 719.5 650 L 720.5 650 L 721.5 780 Z" fill="#1e293b" />
          <circle cx="720" cy="650" r="4" fill="#64748b" />
          {/* Blades group spinning centered on (720, 650) */}
          <g style={{ transformOrigin: '720px 650px' }} className="animate-spin-fast">
            {/* Blade A */}
            <path d="M 719.5 650 C 718.5 590, 719 565, 720 565 C 721 565, 721.5 590, 720.5 650 Z" fill="#64748b" />
            {/* Blade B */}
            <g transform="rotate(120, 720, 650)">
              <path d="M 719.5 650 C 718.5 590, 719 565, 720 565 C 721 565, 721.5 590, 720.5 650 Z" fill="#64748b" />
            </g>
            {/* Blade C */}
            <g transform="rotate(240, 720, 650)">
              <path d="M 719.5 650 C 718.5 590, 719 565, 720 565 C 721 565, 721.5 590, 720.5 650 Z" fill="#64748b" />
            </g>
          </g>
        </g>

        {/* 8. AI NODE NETWORK CONNECTIONS (hidden on mobile) */}
        <g className="hidden sm:block opacity-25" stroke="#10b981" strokeWidth="1" strokeDasharray="3 3">
          {/* Turbine 1 to Turbine 2 */}
          <line x1="1150" y1="550" x2="950" y2="610" />
          {/* Turbine 2 to Central Router */}
          <line x1="950" y1="610" x2="650" y2="760" />
          {/* Central Router to Solar array */}
          <line x1="650" y1="760" x2="310" y2="830" />
          {/* Solar array to far turbine */}
          <line x1="310" y1="830" x2="720" y2="650" strokeWidth="0.75" />
          {/* Turbine 2 to Turbine 3 */}
          <line x1="950" y1="610" x2="720" y2="650" strokeWidth="0.75" />
        </g>

        {/* AI Pulsing Node Indicators */}
        <g className="hidden sm:block">
          <circle cx="1150" cy="550" r="4" fill="#10b981" className="animate-node-pulse" />
          <circle cx="950" cy="610" r="4" fill="#10b981" className="animate-node-pulse" style={{ animationDelay: '1s' }} />
          <circle cx="720" cy="650" r="3.5" fill="#10b981" className="animate-node-pulse" style={{ animationDelay: '2s' }} />
          <circle cx="650" cy="760" r="4.5" fill="#10b981" className="animate-node-pulse" style={{ animationDelay: '1.5s' }} />
          <circle cx="310" cy="830" r="4" fill="#10b981" className="animate-node-pulse" style={{ animationDelay: '0.5s' }} />
        </g>
      </svg>

      {/* 9. SUBTLE FLOATING AMBIENT WIND PARTICLE FLOWS */}
      <div className="absolute inset-0 pointer-events-none opacity-45 z-10 hidden sm:block">
        <div className="absolute top-[28%] left-0 animate-wind-particle-1" style={{ animationDelay: '0s' }}>
          <svg width="240" height="2" viewBox="0 0 240 2" fill="none">
            <path d="M0 1 L240 1" stroke="#f59e0b" strokeWidth="1.5" strokeOpacity="0.4" strokeDasharray="12 8" />
          </svg>
        </div>
        <div className="absolute top-[48%] left-0 animate-wind-particle-2" style={{ animationDelay: '2.5s' }}>
          <svg width="180" height="2" viewBox="0 0 180 2" fill="none">
            <path d="M0 1 L180 1" stroke="#93c5fd" strokeWidth="1.2" strokeOpacity="0.6" strokeDasharray="6 6" />
          </svg>
        </div>
        <div className="absolute top-[68%] left-0 animate-wind-particle-3" style={{ animationDelay: '5s' }}>
          <svg width="200" height="2" viewBox="0 0 200 2" fill="none">
            <path d="M0 1 L200 1" stroke="#10b981" strokeWidth="1.2" strokeOpacity="0.5" strokeDasharray="15 10" />
          </svg>
        </div>
      </div>
    </div>
  );
};
