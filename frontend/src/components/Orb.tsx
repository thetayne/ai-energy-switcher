import React from 'react';
import './Orb.css';

interface OrbProps {
  state: 'waiting' | 'talking';
}

const Orb: React.FC<OrbProps> = ({ state }) => {
  return (
    <div className={`orb orb--${state}`}>
      <svg width="64" height="64">
        <circle cx="32" cy="32" r="24" />
      </svg>
    </div>
  );
};

export default Orb; 