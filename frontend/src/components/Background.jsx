import React from 'react';
import './Background.css';

const Background = () => {
  return (
    <div className="renewable-bg">
      {/* Sun with glow */}
      <div className="sun-core">
        <div className="sun-glow"></div>
      </div>

      {/* Clouds */}
      <div className="cloud cloud-1"></div>
      <div className="cloud cloud-2"></div>
      <div className="cloud cloud-3"></div>

      {/* Wind flow lines */}
      <div className="wind-line w1"></div>
      <div className="wind-line w2"></div>
      <div className="wind-line w3"></div>
      <div className="wind-line w4"></div>
      <div className="wind-line w5"></div>

      {/* Wind Turbines */}
      <div className="turbine turbine-1">
        <div className="tower"></div>
        <div className="nacelle"></div>
        <div className="blades">
          <div className="blade b1"></div>
          <div className="blade b2"></div>
          <div className="blade b3"></div>
        </div>
      </div>

      <div className="turbine turbine-2">
        <div className="tower"></div>
        <div className="nacelle"></div>
        <div className="blades">
          <div className="blade b1"></div>
          <div className="blade b2"></div>
          <div className="blade b3"></div>
        </div>
      </div>

      <div className="turbine turbine-3">
        <div className="tower"></div>
        <div className="nacelle"></div>
        <div className="blades">
          <div className="blade b1"></div>
          <div className="blade b2"></div>
          <div className="blade b3"></div>
        </div>
      </div>

      {/* Solar Panels */}
      <div className="solar-panel sp1">
        <div className="panel-surface">
          <div className="glint"></div>
        </div>
      </div>
      <div className="solar-panel sp2">
        <div className="panel-surface">
          <div className="glint"></div>
        </div>
      </div>

      {/* AI Grid Nodes */}
      <div className="grid-node node-1"></div>
      <div className="grid-node node-2"></div>
      <div className="grid-node node-3"></div>
      <div className="grid-node node-4"></div>
      <div className="grid-node node-5"></div>
      <div className="grid-node node-6"></div>

      {/* Grid Lines */}
      <svg className="grid-lines" viewBox="0 0 1000 600" preserveAspectRatio="none">
        <line x1="100" y1="200" x2="300" y2="100" stroke="rgba(100, 200, 255, 0.2)" strokeWidth="1.5" strokeDasharray="4 6"/>
        <line x1="300" y1="100" x2="500" y2="250" stroke="rgba(100, 200, 255, 0.2)" strokeWidth="1.5" strokeDasharray="4 6"/>
        <line x1="500" y1="250" x2="700" y2="150" stroke="rgba(100, 200, 255, 0.2)" strokeWidth="1.5" strokeDasharray="4 6"/>
        <line x1="700" y1="150" x2="850" y2="300" stroke="rgba(100, 200, 255, 0.2)" strokeWidth="1.5" strokeDasharray="4 6"/>
        <line x1="200" y1="350" x2="400" y2="200" stroke="rgba(100, 200, 255, 0.15)" strokeWidth="1.5" strokeDasharray="4 6"/>
        <line x1="400" y1="200" x2="600" y2="350" stroke="rgba(100, 200, 255, 0.15)" strokeWidth="1.5" strokeDasharray="4 6"/>
        <line x1="600" y1="350" x2="800" y2="250" stroke="rgba(100, 200, 255, 0.15)" strokeWidth="1.5" strokeDasharray="4 6"/>
        <circle cx="100" cy="200" r="4" fill="rgba(100, 200, 255, 0.5)"/>
        <circle cx="300" cy="100" r="4" fill="rgba(100, 200, 255, 0.5)"/>
        <circle cx="500" cy="250" r="4" fill="rgba(100, 200, 255, 0.5)"/>
        <circle cx="700" cy="150" r="4" fill="rgba(100, 200, 255, 0.5)"/>
        <circle cx="850" cy="300" r="4" fill="rgba(100, 200, 255, 0.5)"/>
      </svg>
    </div>
  );
};

export default Background;