import React from 'react';

export interface CapgeminiLogoProps {
  variant?: 'full' | 'spade' | 'badge';
  theme?: 'dark' | 'light';
  height?: number | string;
  className?: string;
  style?: React.CSSProperties;
}

export const CapgeminiLogo: React.FC<CapgeminiLogoProps> = ({
  variant = 'full',
  theme = 'dark',
  height = 32,
  className = '',
  style = {}
}) => {
  const isDark = theme === 'dark';

  if (variant === 'spade') {
    const src = isDark ? '/assets/capgemini-spade.png' : '/assets/capgemini-spade.png';
    return (
      <img
        src={src}
        alt="Capgemini Spade Emblem"
        className={className}
        style={{
          height: height,
          width: 'auto',
          objectFit: 'contain',
          display: 'block',
          ...style
        }}
      />
    );
  }

  if (variant === 'badge') {
    return (
      <div
        className={className}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          ...style
        }}
      >
        <img
          src="/assets/capgemini-spade.png"
          alt="Capgemini Spade"
          style={{
            height: typeof height === 'number' ? height * 0.9 : height,
            width: 'auto',
            objectFit: 'contain',
            flexShrink: 0
          }}
        />
        <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1.15 }}>
          <div style={{
            fontSize: '1.1rem',
            fontWeight: 800,
            color: '#ffffff',
            letterSpacing: '0.5px'
          }}>
            OPSINTEL
          </div>
          <div style={{
            fontSize: '0.625rem',
            fontWeight: 600,
            color: 'var(--cg-blue-vibrant)',
            letterSpacing: '0.06em',
            textTransform: 'uppercase'
          }}>
            Capgemini IT Operations
          </div>
        </div>
      </div>
    );
  }

  // Default 'full' wordmark
  const src = isDark ? '/assets/capgemini-logo-white.png' : '/assets/capgemini-logo.png';
  return (
    <img
      src={src}
      alt="Capgemini"
      className={className}
      style={{
        height: height,
        width: 'auto',
        objectFit: 'contain',
        display: 'block',
        ...style
      }}
    />
  );
};
