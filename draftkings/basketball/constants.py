import os


# Contest Directories
CONTEST_DIR = os.path.join(os.path.dirname((os.path.abspath(__file__))), 'fixtures', 'contests')
CONTEST_BATCH_DIR = os.path.join(CONTEST_DIR, 'batches')
CONTEST_PAGE_DIR = os.path.join(CONTEST_DIR, 'pages')
CONTEST_RESULT_DIR = os.path.join(CONTEST_DIR, 'results')


# Map 3rd party team abbreviations to names used in the database
TEAM_MAP = {
    'NY': 'NYK',
    'NO': 'NOP',
    'PHO': 'PHX',
    'SA': 'SAS',
    'GS': 'GSW',
}


# Map 3rd party player names to names used in the database
PLAYER_MAP = {
    'C.J. McCollum': 'CJ McCollum',
    'J.J. Redick': 'JJ Redick',
    'J.J. Barea': 'Jose Juan Barea',
    'C.J. Watson': 'CJ Watson',
    'T.J. McConnell': 'TJ McConnell',
    'Louis Amundson': 'Lou Amundson',
    'Luc Richard Mbah a Moute': 'Luc Mbah a Moute',
    'C.J. Wilcox': 'CJ Wilcox',
    'R.J. Hunter': 'RJ Hunter',
    'J.J. Hickson': 'JJ Hickson',
    'P.J. Hairston': 'PJ Hairston',
    'T.J. Warren': 'TJ Warren',
    'P.J. Tucker': 'PJ Tucker',
    'Kelly Oubre Jr.': 'Kelly Oubre',
    'K.J. McDaniels': 'KJ McDaniels',
    'C.J. Miles': 'CJ Miles',
    'Glenn Robinson III': 'Glenn Robinson',
    'Jakarr Sampson': 'JaKarr Sampson',
    'Nene Hilario': 'Nene',
    'Timothe Luwawu-Cabarrot': 'Timothe Luwawu',
    'Wade Baldwin IV': 'Wade Baldwin',
    'A.J. Hammons': 'AJ Hammons',
    'Guillermo Hernangomez': 'Willy Hernangomez',
    'Stephen Zimmerman Jr.': 'Stephen Zimmerman',
    'DeAndre\' Bembry': 'DeAndre Bembry',
    'J.R. Smith': 'JR Smith',
    'DeWayne Dedmon': 'Dewayne Dedmon',
}
