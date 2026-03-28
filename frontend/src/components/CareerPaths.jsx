/**
 * components/CareerPaths.jsx — Career Path Suggestion Cards
 * Displays top suggested career paths with match percentage bars.
 */

const CareerPaths = ({ paths = [], missingSkills = [] }) => {
  if (!paths || paths.length === 0) return null;

  return (
    <div className="career-paths">
      <h3 className="section-heading">
        <span className="section-icon">🎯</span> Career Path Suggestions
      </h3>

      <div className="path-cards">
        {paths.slice(0, 5).map((path, i) => (
          <div key={i} className="path-card">
            <div className="path-card-header">
              <span className="path-rank">#{i + 1}</span>
              <h4 className="path-name">{path.name}</h4>
              <span
                className="path-match"
                style={{ color: path.match_pct >= 60 ? '#6fcf97' : path.match_pct >= 30 ? '#f0a060' : '#eb5757' }}
              >
                {path.match_pct}% match
              </span>
            </div>

            {/* Match progress bar */}
            <div className="path-bar-bg">
              <div
                className="path-bar-fill"
                style={{
                  width: `${path.match_pct}%`,
                  background: path.match_pct >= 60
                    ? 'linear-gradient(90deg, #2d8a50, #6fcf97)'
                    : path.match_pct >= 30
                    ? 'linear-gradient(90deg, #8a5a2d, #f0a060)'
                    : 'linear-gradient(90deg, #8a2d2d, #eb5757)',
                }}
              />
            </div>

            <p className="path-desc">{path.desc}</p>

            <div className="path-careers">
              {path.careers?.slice(0, 4).map((c, j) => (
                <span key={j} className="career-pill">{c}</span>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* Missing skills summary */}
      {missingSkills && missingSkills.length > 0 && (
        <div className="missing-block">
          <h4 className="missing-title">
            <span>⚡</span> Skills to Bridge the Gap
          </h4>
          <div className="missing-tags">
            {missingSkills.slice(0, 12).map((skill, i) => (
              <span key={i} className="missing-tag">{skill}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CareerPaths;
