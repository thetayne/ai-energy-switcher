import React from 'react';

type Provider = {
  name: string;
  price: string;
  reason: string;
};

interface RecommendationsProps {
  providers: Provider[];
}

const Recommendations: React.FC<RecommendationsProps> = ({ providers }) => {
  return (
    <div className="recommendations">
      <h2>Our Top 3 Recommendations</h2>
      <ul>
        {providers.map((p, idx) => (
          <li key={p.name} className="provider-card">
            <h3>{idx + 1}. {p.name}</h3>
            <p><strong>Price:</strong> {p.price}</p>
            <p><strong>Why?</strong> {p.reason}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default Recommendations; 