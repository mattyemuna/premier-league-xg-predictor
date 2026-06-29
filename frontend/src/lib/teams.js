export const TEAM_ABBR = {
  'Arsenal':                   'ARS',
  'Aston Villa':               'AVL',
  'Bournemouth':               'BOU',
  'Brentford':                 'BRE',
  'Brighton':                  'BHA',
  'Burnley':                   'BUR',
  'Chelsea':                   'CHE',
  'Crystal Palace':            'CRY',
  'Everton':                   'EVE',
  'Fulham':                    'FUL',
  'Ipswich':                   'IPS',
  'Leeds':                     'LEE',
  'Leicester':                 'LEI',
  'Liverpool':                 'LIV',
  'Luton':                     'LUT',
  'Manchester City':           'MCI',
  'Manchester United':         'MUN',
  'Newcastle United':          'NEW',
  'Norwich':                   'NOR',
  'Nottingham Forest':         'NFO',
  'Sheffield United':          'SHU',
  'Southampton':               'SOU',
  'Sunderland':                'SUN',
  'Tottenham':                 'TOT',
  'Watford':                   'WAT',
  'West Ham':                  'WHU',
  'Wolverhampton Wanderers':   'WOL',
}

// Muted club hues for the identity badge (low-opacity fill, slightly more opaque stroke)
export const TEAM_HUE = {
  'Arsenal':                  '#EF0107',
  'Aston Villa':              '#670E36',
  'Bournemouth':              '#DA291C',
  'Brentford':                '#E30613',
  'Brighton':                 '#0057B8',
  'Burnley':                  '#6C1D45',
  'Chelsea':                  '#034694',
  'Crystal Palace':           '#1B458F',
  'Everton':                  '#003399',
  'Fulham':                   '#CC0000',
  'Ipswich':                  '#0044A9',
  'Leeds':                    '#B5A300',
  'Leicester':                '#003090',
  'Liverpool':                '#C8102E',
  'Luton':                    '#F07A00',
  'Manchester City':          '#5FABE2',
  'Manchester United':        '#DA291C',
  'Newcastle United':         '#41B6E6',
  'Norwich':                  '#00A650',
  'Nottingham Forest':        '#DD0000',
  'Sheffield United':         '#EE2737',
  'Southampton':              '#D71920',
  'Sunderland':               '#EB172B',
  'Tottenham':                '#132257',
  'Watford':                  '#BFA100',
  'West Ham':                 '#7A263A',
  'Wolverhampton Wanderers':  '#D4A800',
}

export function getAbbr(team) {
  return TEAM_ABBR[team] ?? team.slice(0, 3).toUpperCase()
}

export function getHue(team) {
  return TEAM_HUE[team] ?? '#8A909C'
}

export function formatDate(iso) {
  if (!iso) return ''
  const d = new Date(iso + 'T00:00:00')
  return d.toLocaleDateString('en-GB', { weekday: 'short', day: 'numeric', month: 'short' })
}
