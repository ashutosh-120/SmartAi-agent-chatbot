/**
 * components/SkillCard.jsx — Skill Tag/Badge Component
 * Renders a single skill as a colored pill with category-based color coding.
 */

const CATEGORY_COLORS = {
  Languages:  { bg: '#1a3a5c', border: '#2d6a9f', text: '#7ec8e3' },
  Frameworks: { bg: '#1a3d2b', border: '#2d8a50', text: '#6fcf97' },
  Domain:     { bg: '#3d1a3d', border: '#8a2d8a', text: '#da77da' },
  Practices:  { bg: '#3d2a1a', border: '#8a5a2d', text: '#f0a060' },
  Tools:      { bg: '#1a2d3d', border: '#2d5080', text: '#78b4e0' },
  Other:      { bg: '#2a2a2a', border: '#555',    text: '#aaa'    },
};

/**
 * @param {string} skill    — skill name
 * @param {string} category — skill category (for color)
 * @param {number} [score]  — optional 0-100 score to show as mini badge
 */
const SkillCard = ({ skill, category = 'Other', score }) => {
  const colors = CATEGORY_COLORS[category] || CATEGORY_COLORS.Other;

  return (
    <span
      className="skill-tag"
      style={{
        background:   colors.bg,
        border:       `1px solid ${colors.border}`,
        color:        colors.text,
      }}
      title={`${category}${score !== undefined ? ` • Score: ${score}` : ''}`}
    >
      {skill}
      {score !== undefined && (
        <span className="skill-score-badge">{score}</span>
      )}
    </span>
  );
};

export default SkillCard;
