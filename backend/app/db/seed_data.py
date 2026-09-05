import datetime
from sqlalchemy.orm import Session
from app.db.models import PublisherCredibility, TrendingClaim, ClaimHistory

INITIAL_PUBLISHERS = [
    # Top Tier Fact Checkers (Credibility 95-98)
    {"domain": "snopes.com", "name": "Snopes", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 98, "country": "USA", "notes": "One of the oldest and most respected fact-checking organizations."},
    {"domain": "politifact.com", "name": "PolitiFact", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 97, "country": "USA", "notes": "Pulitzer Prize-winning fact-checking initiative by Poynter."},
    {"domain": "factcheck.org", "name": "FactCheck.org", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 98, "country": "USA", "notes": "Project of the Annenberg Public Policy Center of the University of Pennsylvania."},
    {"domain": "fullfact.org", "name": "Full Fact", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 96, "country": "UK", "notes": "UK's independent fact-checking charity."},
    {"domain": "afp.com", "name": "AFP Fact Check", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 98, "country": "Global", "notes": "Global fact-checking division of Agence France-Presse."},
    {"domain": "reuters.com", "name": "Reuters Fact Check", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 99, "country": "Global", "notes": "Dedicated investigative fact-checking unit of Reuters."},
    {"domain": "apnews.com", "name": "Associated Press Fact Check", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 99, "country": "Global", "notes": "AP's global team debunking misleading assertions."},
    {"domain": "leadstories.com", "name": "Lead Stories", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "High", "credibility_score": 94, "country": "USA", "notes": "Poynter-certified IFCN signatory fact-checking viral hoaxes."},
    {"domain": "checkyourfact.com", "name": "Check Your Fact", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "High", "credibility_score": 92, "country": "USA", "notes": "IFCN-certified fact-checking operation."},
    {"domain": "healthfeedback.org", "name": "Health Feedback", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 98, "country": "Global", "notes": "Scientific network dedicated to verifying health and medical claims."},
    {"domain": "climatefeedback.org", "name": "Climate Feedback", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 98, "country": "Global", "notes": "Accredited scientists assessing climate science accuracy."},
    {"domain": "sciencefeedback.co", "name": "Science Feedback", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 98, "country": "Global", "notes": "Peer-reviewed scientist fact-checking network."},
    {"domain": "altnews.in", "name": "Alt News", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "High", "credibility_score": 93, "country": "India", "notes": "Non-profit fact-checking website."},
    {"domain": "boomlive.in", "name": "BOOM Live", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "High", "credibility_score": 94, "country": "India", "notes": "IFCN accredited fact checker."},
    {"domain": "thejournal.ie", "name": "TheJournal.ie FactCheck", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "High", "credibility_score": 93, "country": "Ireland", "notes": "IFCN certified newsroom."},
    {"domain": "lemonde.fr", "name": "Les Décodeurs (Le Monde)", "category": "Fact-Checker", "bias_rating": "Lean Left", "factual_reporting": "Very High", "credibility_score": 95, "country": "France", "notes": "Fact-checking desk of Le Monde."},
    {"domain": "correctiv.org", "name": "Correctiv", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 96, "country": "Germany", "notes": "Non-profit investigative newsroom."},
    {"domain": "chequeado.com", "name": "Chequeado", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 96, "country": "Argentina", "notes": "Pioneer Latin American fact-checking organization."},
    {"domain": "africacheck.org", "name": "Africa Check", "category": "Fact-Checker", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 97, "country": "Africa", "notes": "Africa's first independent non-partisan fact-checking organization."},

    # High Credibility Mainstream & Scientific Sources (Credibility 85-98)
    {"domain": "bbc.com", "name": "BBC News", "category": "Mainstream", "bias_rating": "Center", "factual_reporting": "High", "credibility_score": 93, "country": "UK", "notes": "British public service broadcaster."},
    {"domain": "bbc.co.uk", "name": "BBC", "category": "Mainstream", "bias_rating": "Center", "factual_reporting": "High", "credibility_score": 93, "country": "UK", "notes": "UK national broadcaster."},
    {"domain": "nature.com", "name": "Nature", "category": "Mainstream", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 99, "country": "Global", "notes": "Peer-reviewed scientific journal."},
    {"domain": "sciencemag.org", "name": "Science / AAAS", "category": "Mainstream", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 99, "country": "Global", "notes": "American Association for the Advancement of Science."},
    {"domain": "science.org", "name": "Science.org", "category": "Mainstream", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 99, "country": "Global", "notes": "Flagship scientific publication."},
    {"domain": "nasa.gov", "name": "NASA", "category": "Mainstream", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 99, "country": "USA", "notes": "National Aeronautics and Space Administration."},
    {"domain": "who.int", "name": "World Health Organization", "category": "Mainstream", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 97, "country": "Global", "notes": "UN specialized agency for international public health."},
    {"domain": "cdc.gov", "name": "Centers for Disease Control and Prevention", "category": "Mainstream", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 97, "country": "USA", "notes": "US national public health agency."},
    {"domain": "nih.gov", "name": "National Institutes of Health", "category": "Mainstream", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 98, "country": "USA", "notes": "Primary agency of the US government responsible for biomedical research."},
    {"domain": "nytimes.com", "name": "The New York Times", "category": "Mainstream", "bias_rating": "Lean Left", "factual_reporting": "High", "credibility_score": 90, "country": "USA", "notes": "Major US daily newspaper with rigorous reporting standards."},
    {"domain": "washingtonpost.com", "name": "The Washington Post", "category": "Mainstream", "bias_rating": "Lean Left", "factual_reporting": "High", "credibility_score": 89, "country": "USA", "notes": "Major US daily newspaper."},
    {"domain": "wsj.com", "name": "The Wall Street Journal", "category": "Mainstream", "bias_rating": "Lean Right", "factual_reporting": "High", "credibility_score": 91, "country": "USA", "notes": "Leading business and financial daily."},
    {"domain": "theguardian.com", "name": "The Guardian", "category": "Mainstream", "bias_rating": "Lean Left", "factual_reporting": "High", "credibility_score": 88, "country": "UK", "notes": "British news and media organization."},
    {"domain": "economist.com", "name": "The Economist", "category": "Mainstream", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 94, "country": "UK", "notes": "Weekly newsmagazine focusing on global economy and politics."},
    {"domain": "npr.org", "name": "National Public Radio (NPR)", "category": "Mainstream", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 94, "country": "USA", "notes": "Non-profit media organization."},
    {"domain": "bloomberg.com", "name": "Bloomberg", "category": "Mainstream", "bias_rating": "Center", "factual_reporting": "High", "credibility_score": 92, "country": "USA", "notes": "Global business, financial information and news."},
    {"domain": "ft.com", "name": "Financial Times", "category": "Mainstream", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 95, "country": "UK", "notes": "International business and economic daily."},
    {"domain": "scientificamerican.com", "name": "Scientific American", "category": "Mainstream", "bias_rating": "Lean Left", "factual_reporting": "Very High", "credibility_score": 94, "country": "USA", "notes": "Popular science magazine published since 1845."},
    {"domain": "nationalgeographic.com", "name": "National Geographic", "category": "Mainstream", "bias_rating": "Center", "factual_reporting": "Very High", "credibility_score": 95, "country": "USA", "notes": "Scientific and educational organization."},

    # Known Satire Websites (Credibility 70 - Clearly Labeled Satire)
    {"domain": "theonion.com", "name": "The Onion", "category": "Satire", "bias_rating": "Satire", "factual_reporting": "Satire", "credibility_score": 60, "country": "USA", "notes": "Famous American digital media company and news satire organization."},
    {"domain": "babylonbee.com", "name": "The Babylon Bee", "category": "Satire", "bias_rating": "Satire", "factual_reporting": "Satire", "credibility_score": 60, "country": "USA", "notes": "Conservative Christian news satire website."},
    {"domain": "newsthump.com", "name": "NewsThump", "category": "Satire", "bias_rating": "Satire", "factual_reporting": "Satire", "credibility_score": 60, "country": "UK", "notes": "UK satirical news site."},
    {"domain": "thebeaverton.com", "name": "The Beaverton", "category": "Satire", "bias_rating": "Satire", "factual_reporting": "Satire", "credibility_score": 60, "country": "Canada", "notes": "Canadian news satire publication."},
    {"domain": "waterfordwhispersnews.com", "name": "Waterford Whispers News", "category": "Satire", "bias_rating": "Satire", "factual_reporting": "Satire", "credibility_score": 60, "country": "Ireland", "notes": "Irish satirical news website."},
    {"domain": "thepoke.co.uk", "name": "The Poke", "category": "Satire", "bias_rating": "Satire", "factual_reporting": "Satire", "credibility_score": 60, "country": "UK", "notes": "British satirical website."},
    {"domain": "clickhole.com", "name": "ClickHole", "category": "Satire", "bias_rating": "Satire", "factual_reporting": "Satire", "credibility_score": 60, "country": "USA", "notes": "Satire website parodying clickbait web content."},

    # Known Misinformation / Low Credibility / Conspiracy Outlets (Credibility 10-35)
    {"domain": "infowars.com", "name": "InfoWars", "category": "Conspiracy/Fake", "bias_rating": "Extreme", "factual_reporting": "Very Low", "credibility_score": 12, "country": "USA", "notes": "Conspiracy theory and fake news website operated by Alex Jones."},
    {"domain": "naturalnews.com", "name": "Natural News", "category": "Conspiracy/Fake", "bias_rating": "Extreme", "factual_reporting": "Very Low", "credibility_score": 10, "country": "USA", "notes": "Known for anti-vaccination conspiracy theories and bogus health remedies."},
    {"domain": "thegatewaypundit.com", "name": "The Gateway Pundit", "category": "Conspiracy/Fake", "bias_rating": "Extreme", "factual_reporting": "Low", "credibility_score": 20, "country": "USA", "notes": "Frequently publishes false information, hoaxes, and conspiracy theories."},
    {"domain": "beforeitsnews.com", "name": "Before It's News", "category": "Conspiracy/Fake", "bias_rating": "Extreme", "factual_reporting": "Very Low", "credibility_score": 8, "country": "USA", "notes": "Unmoderated user-submitted conspiracy blog network."},
    {"domain": "worldnewsdailyreport.com", "name": "World News Daily Report", "category": "Conspiracy/Fake", "bias_rating": "Extreme", "factual_reporting": "Very Low", "credibility_score": 5, "country": "USA", "notes": "Fabricated fake news website creating deceptive stories."},
    {"domain": "newspunch.com", "name": "NewsPunch (YourNewsWire)", "category": "Conspiracy/Fake", "bias_rating": "Extreme", "factual_reporting": "Very Low", "credibility_score": 8, "country": "USA", "notes": "Prolific publisher of fake news stories and conspiracy theories."},
    {"domain": "rt.com", "name": "RT (Russia Today)", "category": "State-Sponsored", "bias_rating": "Right", "factual_reporting": "Low", "credibility_score": 30, "country": "Russia", "notes": "Russian state-controlled international news television network."},
    {"domain": "sputniknews.com", "name": "Sputnik News", "category": "State-Sponsored", "bias_rating": "Right", "factual_reporting": "Low", "credibility_score": 28, "country": "Russia", "notes": "Russian state-owned news agency."},
    {"domain": "theepochtimes.com", "name": "The Epoch Times", "category": "Conspiracy/Fake", "bias_rating": "Right", "factual_reporting": "Low", "credibility_score": 35, "country": "USA", "notes": "Known for promoting conspiracy theories and unsubstantiated claims."},
    {"domain": "zerohedge.com", "name": "ZeroHedge", "category": "Conspiracy/Fake", "bias_rating": "Right", "factual_reporting": "Mixed", "credibility_score": 42, "country": "USA", "notes": "Financial blog that regularly aggregates conspiracy content and unvetted claims."}
]

INITIAL_TRENDING_CLAIMS = [
    {
        "claim_text": "Drinking boiled garlic water cures and prevents coronavirus and viral infections.",
        "verdict": "False",
        "confidence": 98.0,
        "category": "Health & Medicine",
        "summary": "Medical experts and the World Health Organization (WHO) confirm that while garlic has mild antimicrobial properties, there is zero scientific evidence that consuming garlic or garlic water prevents or cures viral infections.",
        "source_name": "WHO & Health Feedback",
        "source_url": "https://www.who.int/emergencies/diseases/novel-coronavirus-2019/advice-for-public/myth-busters",
        "search_volume": 1420
    },
    {
        "claim_text": "NASA's James Webb Space Telescope detected atmospheric water vapor on exoplanet WASP-96b.",
        "verdict": "True",
        "confidence": 99.0,
        "category": "Science & Space",
        "summary": "NASA, ESA, and CSA confirmed that the James Webb Space Telescope captured the distinct signature of water, along with evidence for clouds and haze, in the atmosphere surrounding the hot gas giant WASP-96b.",
        "source_name": "NASA & Nature",
        "source_url": "https://www.nasa.gov/image-article/nasas-webb-reveals-steamy-atmosphere-on-distant-gas-giant-planet/",
        "search_volume": 1280
    },
    {
        "claim_text": "5G mobile network radiation causes viral respiratory illnesses.",
        "verdict": "False",
        "confidence": 99.0,
        "category": "Technology & Science",
        "summary": "Biological viruses cannot travel through radio waves or mobile networks. 5G uses non-ionizing electromagnetic radiation, which cannot create biological pathogens.",
        "source_name": "Full Fact & AP News",
        "source_url": "https://fullfact.org/online/5g-coronavirus-immune-system/",
        "search_volume": 1950
    },
    {
        "claim_text": "Pope Francis officially endorsed Donald Trump for US President.",
        "verdict": "False",
        "confidence": 97.0,
        "category": "Politics",
        "summary": "The Vatican and official papal spokespeople confirmed the Pope maintains strict neutrality in national elections and never made any political endorsement.",
        "source_name": "Snopes & Reuters Fact Check",
        "source_url": "https://www.snopes.com/fact-check/pope-francis-donald-trump-endorsement/",
        "search_volume": 980
    },
    {
        "claim_text": "Eating ripe bananas with dark patches produces TNF that destroys cancer cells.",
        "verdict": "False",
        "confidence": 96.0,
        "category": "Health & Medicine",
        "summary": "A viral chain message claimed ripe bananas produce Tumor Necrosis Factor (TNF) to fight cancer. Cancer research scientists confirmed ripe bananas contain natural fruit ripening enzymes, not anti-cancer human cytokines.",
        "source_name": "FactCheck.org & Health Feedback",
        "source_url": "https://www.factcheck.org/2019/07/viral-claim-about-bananas-and-cancer-is-bogus/",
        "search_volume": 1100
    },
    {
        "claim_text": "NASA astronauts discovered alien pyramids built under the surface of Mars.",
        "verdict": "False",
        "confidence": 98.0,
        "category": "Science & Space",
        "summary": "Geological formations photographed on Mars are natural erosional features and ventifacts. No evidence of artificial alien structures has ever been detected by rovers or orbiters.",
        "source_name": "Reuters Fact Check & NASA",
        "source_url": "https://www.reuters.com/article/factcheck-nasa-pyramid-mars-idUSL1N2T61A8/",
        "search_volume": 840
    },
    {
        "claim_text": "Electric cars produce more lifetime carbon emissions than conventional gasoline vehicles.",
        "verdict": "Misleading",
        "confidence": 91.0,
        "category": "Climate & Energy",
        "summary": "While EV battery manufacturing has an upfront carbon footprint, comprehensive lifecycle analyses (ICCT, BloombergNEF, MIT) demonstrate EVs generate 50% to 70% fewer net emissions over their lifetime compared to gas cars on almost all global electric grids.",
        "source_name": "PolitiFact & International Council on Clean Transportation",
        "source_url": "https://www.politifact.com/factchecks/2021/may/11/environmental-protection-agency/yes-electric-vehicles-are-cleaner-gasoline-cars-e/",
        "search_volume": 1310
    },
    {
        "claim_text": "NASA announces the moon is entirely hollow and inhabited by ancient robot miners.",
        "verdict": "Satire",
        "confidence": 99.0,
        "category": "Satire & Humor",
        "summary": "This claim originated as an article from the satirical humor website The Onion and was reshared on social media without satire disclaimer context.",
        "source_name": "The Onion (Satire)",
        "source_url": "https://www.theonion.com/",
        "search_volume": 760
    }
]

def seed_database(db: Session):
    # Check if publishers already exist
    existing_pubs = db.query(PublisherCredibility).count()
    if existing_pubs == 0:
        for pub_data in INITIAL_PUBLISHERS:
            db.add(PublisherCredibility(**pub_data))
        db.commit()
    
    # Check if trending claims exist
    existing_trending = db.query(TrendingClaim).count()
    if existing_trending == 0:
        for trend in INITIAL_TRENDING_CLAIMS:
            db.add(TrendingClaim(**trend))
        db.commit()

    # Seed some initial history if empty
    existing_history = db.query(ClaimHistory).count()
    if existing_history == 0:
        for trend in INITIAL_TRENDING_CLAIMS[:5]:
            db.add(ClaimHistory(
                input_text=trend["claim_text"],
                extracted_claim=trend["claim_text"],
                verdict=trend["verdict"],
                confidence=trend["confidence"],
                category=trend["category"],
                sources_count=2,
                red_flag_score=85.0 if trend["verdict"] == "False" else 15.0,
                explanation_summary=trend["summary"],
                created_at=datetime.datetime.utcnow() - datetime.timedelta(hours=5)
            ))
        db.commit()
