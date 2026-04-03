from django.utils.translation import gettext_lazy as _

MENS_SERVICES = [
    {
        'category': _('Hair Services'),
        'icon': 'fas fa-cut',
        'services': [
            _('Basic haircut (classic cut)'),
            _('Model haircut (modern style)'),
            _('Fade (low, mid, high fade)'),
            _('Skin fade (zero fade)'),
            _('Clipper haircut'),
            _('Scissor haircut'),
            _('Kids haircut'),
            _('Hair trimming'),
            _('Hair washing'),
            _('Blow-dry styling'),
        ]
    },
    {
        'category': _('Beard Services'),
        'icon': 'fas fa-soap',
        'services': [
            _('Full shave (clean shave)'),
            _('Beard shaping (line-up / contour)'),
            _('Beard trimming (with trimmer)'),
            _('Hot towel shave'),
            _('Beard coloring'),
        ]
    },
    {
        'category': _('Styling & Hair Care'),
        'icon': 'fas fa-magic',
        'services': [
            _('Applying gel / wax / pomade'),
            _('Professional hair styling'),
            _('Hair coloring'),
            _('Hair bleaching'),
            _('Keratin treatment (hair straightening)'),
            _('Hair treatment (masks, repair care)'),
        ]
    },
    {
        'category': _('Face & Skin Care'),
        'icon': 'fas fa-pump-soap',
        'services': [
            _('Facial cleansing'),
            _('Blackhead removal'),
            _('Facial scrub'),
            _('Face mask'),
            _('Facial massage'),
        ]
    },
    {
        'category': _('Additional Services'),
        'icon': 'fas fa-plus-circle',
        'services': [
            _('Ear hair removal'),
            _('Nose hair removal'),
            _('Eyebrow grooming'),
            _('Head massage'),
            _('Neck massage'),
        ]
    },
    {
        'category': _('Premium Services'),
        'icon': 'fas fa-crown',
        'services': [
            _('SPA services'),
            _('VIP room service'),
            _('Full grooming package (hair + beard + facial)'),
            _('Aromatherapy'),
        ]
    },
    {
        'category': _('Service Packages'),
        'icon': 'fas fa-box',
        'services': [
            _('Hair + beard combo (most popular)'),
            _('Full grooming package'),
            _('Special occasion (wedding/event package)'),
        ]
    },
]

WOMENS_SERVICES = [
    {
        'category': _('Hair Services'),
        'icon': 'fas fa-cut',
        'services': [
            _('Haircut (basic and model cuts)'),
            _('Trimming split ends'),
            _('Layered haircut'),
            _('Bangs (fringe) styling'),
            _('Hair washing'),
            _('Blow-dry (brushing)'),
            _('Hair styling'),
            _('Evening / wedding hairstyles (updos)'),
        ]
    },
    {
        'category': _('Hair Coloring Services'),
        'icon': 'fas fa-palette',
        'services': [
            _('Full hair coloring'),
            _('Root touch-up'),
            _('Highlights (melirovka)'),
            _('Ombre'),
            _('Balayage'),
            _('Airtouch'),
            _('Bleaching'),
            _('Toning'),
        ]
    },
    {
        'category': _('✨ Hair Care & Treatment'),
        'icon': 'fas fa-magic',
        'services': [
            _('Keratin treatment (hair straightening)'),
            _('Hair botox treatment'),
            _('Hair lamination'),
            _('Hair masks'),
            _('Protein treatment'),
            _('Hot oil treatment'),
            _('Scalp treatment'),
        ]
    },
    {
        'category': _('Nail Services (Manicure & Pedicure)'),
        'icon': 'fas fa-hand-holding-heart',
        'services': [
            _('Classic manicure'),
            _('Machine manicure (apparat)'),
            _('Gel polish (shellac)'),
            _('Nail extensions'),
            _('Nail art (design)'),
            _('Pedicure'),
            _('SPA manicure / pedicure'),
        ]
    },
    {
        'category': _('Face & Skin Care'),
        'icon': 'fas fa-spa',
        'services': [
            _('Facial cleansing'),
            _('Deep cleansing'),
            _('Blackhead removal'),
            _('Peeling'),
            _('Scrub'),
            _('Face masks'),
            _('Anti-aging treatments'),
            _('Facial massage'),
        ]
    },
    {
        'category': _('Eyebrow & Eyelash Services'),
        'icon': 'fas fa-eye',
        'services': [
            _('Eyebrow shaping'),
            _('Eyebrow tinting'),
            _('Henna brows'),
            _('Brow & lash lamination'),
            _('Eyelash extensions'),
            _('Eyelash tinting'),
            _('Lash lifting'),
        ]
    },
    {
        'category': _('Make-up Services'),
        'icon': 'fas fa-paint-brush',
        'services': [
            _('Day makeup'),
            _('Evening makeup'),
            _('Bridal makeup'),
            _('Photo / video makeup'),
            _('Contouring & highlighting'),
        ]
    },
    {
        'category': _('Hair Removal Services'),
        'icon': 'fas fa-wind',
        'services': [
            _('Waxing'),
            _('Sugaring'),
            _('Laser hair removal'),
            _('Arms, legs, face, bikini area'),
        ]
    },
    {
        'category': _('Massage & SPA Services'),
        'icon': 'fas fa-spa',
        'services': [
            _('Facial massage'),
            _('Body massage'),
            _('Relax massage'),
            _('SPA treatments'),
            _('Aromatherapy'),
        ]
    },
    {
        'category': _('Special Services'),
        'icon': 'fas fa-gem',
        'services': [
            _('Bridal full package (hair + makeup)'),
            _('Event / party preparation'),
            _('Photoshoot styling'),
        ]
    },
]
