"""
Sources module - Contains all source scrapers
"""

from .african_union import AfricanUnionScraper
from .united_nations import UnitedNationsScraper
from .world_bank import WorldBankScraper
from .african_development_bank import AfricanDevelopmentBankScraper
from .mastercard import MastercardScraper
from .google import GoogleScraper
from .microsoft import MicrosoftScraper
from .youthhub import YouthHubScraper
from .opportunities_for_africa import OpportunitiesForAfricaScraper
from .unicef import UNICEFScraper
from .unesco import UNESCOScraper
from .undp import UNDPScraper
from .british_council import BritishCouncilScraper
from .commonwealth import CommonwealthScraper

__all__ = [
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
