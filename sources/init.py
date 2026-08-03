"""
Sources module - Contains all source scrapers
"""

from .base_scraper import BaseScraper
from .source_manager import SourceManager

# Try to import all scrapers, but don't fail if any are missing
try:
    from .african_union import AfricanUnionScraper
except ImportError:
    AfricanUnionScraper = None

try:
    from .united_nations import UnitedNationsScraper
except ImportError:
    UnitedNationsScraper = None

try:
    from .world_bank import WorldBankScraper
except ImportError:
    WorldBankScraper = None

try:
    from .african_development_bank import AfricanDevelopmentBankScraper
except ImportError:
    AfricanDevelopmentBankScraper = None

try:
    from .mastercard import MastercardScraper
except ImportError:
    MastercardScraper = None

try:
    from .google import GoogleScraper
except ImportError:
    GoogleScraper = None

try:
    from .microsoft import MicrosoftScraper
except ImportError:
    MicrosoftScraper = None

try:
    from .youthhub import YouthHubScraper
except ImportError:
    YouthHubScraper = None

try:
    from .opportunities_for_africa import OpportunitiesForAfricaScraper
except ImportError:
    OpportunitiesForAfricaScraper = None

try:
    from .unicef import UNICEFScraper
except ImportError:
    UNICEFScraper = None

try:
    from .unesco import UNESCOScraper
except ImportError:
    UNESCOScraper = None

try:
    from .undp import UNDPScraper
except ImportError:
    UNDPScraper = None

try:
    from .british_council import BritishCouncilScraper
except ImportError:
    BritishCouncilScraper = None

try:
    from .commonwealth import CommonwealthScraper
except ImportError:
    CommonwealthScraper = None

__all__ = [
    'BaseScraper',
    'SourceManager',
    'AfricanUnionScraper',
    'UnitedNationsScraper',
    'WorldBankScraper',
    'AfricanDevelopmentBankScraper',
    'MastercardScraper',
    'GoogleScraper',
    'MicrosoftScraper',
    'YouthHubScraper',
    'OpportunitiesForAfricaScraper',
    'UNICEFScraper',
    'UNESCOScraper',
    'UNDPScraper',
    'BritishCouncilScraper',
    'CommonwealthScraper'
]
