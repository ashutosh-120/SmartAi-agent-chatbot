/**
 * components/RoadmapTimeline.jsx — Week-by-Week Roadmap Timeline
 * Parses the Gemini-generated markdown roadmap into structured week cards.
 */

import { useState } from 'react';

/**
 * Parse the roadmap markdown string into an array of week objects.
 * Looks for patterns like: ## Week 1: Title
 */
const parseWeeks = (roadmapText) => {
  if (!roadmapText) return [];

  const weekRegex = /##\s+Week\s+(\d+)[:\s]+([^\n]+)\n([\s\S]*?)(?=##\s+Week\s+\d+|##\s+Recommended|##\s+Capstone|##\s+Success|$)/gi;
  const weeks = [];
  let match;

  while ((match = weekRegex.exec(roadmapText)) !== null) {
    const weekNum = parseInt(match[1]);
    const title   = match[2].trim().replace(/\*+/g, '');
    const body    = match[3].trim();

    // Extract focus, learn items, project, resources from body
    const focus     = (body.match(/\*\*Focus:\*\*\s*([^\n]+)/) || [])[1]?.trim() || '';
    const project   = (body.match(/\*\*Project:\*\*\s*([^\n]+)/) || [])[1]?.trim() || '';
    const resources = (body.match(/\*\*Resources:\*\*\s*([^\n]+)/) || [])[1]?.trim() || '';

    // Extract bullet points under **Learn:**
    const learnMatch = body.match(/\*\*Learn:\*\*\s*([\s\S]*?)(?=\*\*Project|\*\*Resources|$)/);
    const learnItems = learnMatch
      ? learnMatch[1].match(/^[-*]\s+(.+)$/mg)?.map(l => l.replace(/^[-*]\s+/, '').trim()) || []
      : [];

    weeks.push({ weekNum, title, focus, learnItems, project, resources });
  }

  return weeks;
};

/** Extract the overview section from roadmap markdown */
const parseOverview = (roadmapText) => {
  const match = roadmapText?.match(/##\s+Overview\s*\n([\s\S]*?)(?=##|$)/i);
  return match ? match[1].trim() : '';
};

/** Extract the capstone project section */
const parseCapstone = (roadmapText) => {
  const match = roadmapText?.match(/##\s+(?:Final\s+)?Capstone\s+Project\s*\n([\s\S]*?)(?=##|$)/i);
  return match ? match[1].trim() : '';
};

const RoadmapTimeline = ({ roadmap }) => {
  const [expanded, setExpanded] = useState(null);

  if (!roadmap) return null;

  const weeks    = parseWeeks(roadmap);
  const overview = parseOverview(roadmap);
  const capstone = parseCapstone(roadmap);

  // If we can't parse weeks, show the raw markdown
  if (weeks.length === 0) {
    return (
      <div className="roadmap-raw">
        <h3 className="section-heading"><span className="section-icon">🗺️</span> Learning Roadmap</h3>
        <div className="roadmap-markdown" dangerouslySetInnerHTML={{
          __html: roadmap.replace(/\n/g, '<br/>').replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        }} />
      </div>
    );
  }

  return (
    <div className="roadmap-timeline">
      <h3 className="section-heading">
        <span className="section-icon">🗺️</span> Learning Roadmap
        <span className="week-count">{weeks.length} weeks</span>
      </h3>

      {overview && <p className="roadmap-overview">{overview}</p>}

      {/* Week cards */}
      <div className="timeline-container">
        {weeks.map((week, i) => (
          <div
            key={i}
            className={`week-card ${expanded === i ? 'expanded' : ''}`}
            onClick={() => setExpanded(expanded === i ? null : i)}
          >
            {/* Timeline connector */}
            <div className="timeline-connector">
              <div className="timeline-dot">{week.weekNum}</div>
              {i < weeks.length - 1 && <div className="timeline-line" />}
            </div>

            <div className="week-content">
              <div className="week-header">
                <h4 className="week-title">Week {week.weekNum}: {week.title}</h4>
                <span className="expand-icon">{expanded === i ? '▲' : '▼'}</span>
              </div>

              {week.focus && (
                <p className="week-focus">
                  <span className="label">Focus:</span> {week.focus}
                </p>
              )}

              {expanded === i && (
                <div className="week-details">
                  {week.learnItems.length > 0 && (
                    <div className="week-learn">
                      <span className="label">📚 Learn:</span>
                      <ul>
                        {week.learnItems.map((item, j) => (
                          <li key={j}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                  {week.project && (
                    <p className="week-project">
                      <span className="label">🛠️ Project:</span> {week.project}
                    </p>
                  )}
                  {week.resources && (
                    <p className="week-resources">
                      <span className="label">🔗 Resources:</span> {week.resources}
                    </p>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>

      {capstone && (
        <div className="capstone-card">
          <h4>🚀 Capstone Project</h4>
          <p>{capstone}</p>
        </div>
      )}
    </div>
  );
};

export default RoadmapTimeline;
