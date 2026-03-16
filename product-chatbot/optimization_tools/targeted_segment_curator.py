import json
import re
from pathlib import Path
from typing import Any

import requests
from dotenv import dotenv_values


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"
RAW_HEADER = "## 📄 [RAW ORIGINAL TEXT]"
AI_HEADER = "## 🤖 [AI OPTIMIZED STRUCTURED DATA]"
LOCAL_DIFY_FALLBACK = "http://172.19.0.10:5001/v1"
DOCUMENT_ID = "e03cb834-ef07-4073-88ba-78b6fa5effc5"
DATASET_ID = "ef2d93fa-1db9-4e22-8d3b-7a26b9ab0504"


FIXES: dict[int, dict[str, Any]] = {
    36: {
        "product_name": "Assurance TripleMax 2",
        "category": "Passenger",
        "target_audience": "Drivers seeking improved safety and confidence",
        "features": [
            "Optimized for excellent grip.",
            "Shorter wet braking distance improves safety and confidence.",
            "Asymmetrical tread design supports wet braking performance.",
            "HydroTred technology is the key wet-braking technology for this product.",
        ],
        "performance_charts": [
            "Superior wet braking performance with HydroTred technology.",
        ],
        "technology_descriptions": [
            "HydroTred technology improves wet-road braking performance.",
            "This product is Assurance TripleMax 2 and must not use Assurance TripleMax technology names such as Functionalized Polymer Tread Compound, Wide Face Cavity, or Biting Edges.",
        ],
        "sizes": [
            "175/65R14 82H","175/65R14 82T","175/70R14 84H","185/60R14 82H","185/65R14 86H","195/60R14 86H","195/65R14 89H","175/65R15 84T","185/55R15 82V","185/60R15 84H","185/65R15 88H","195/50R15 82V","195/55R15 85V","195/60R15 88H","195/65R15 91H","205/65R15 94V","185/55R16 83V","185/60R16 86H","195/50R16 84V","195/55R16 87H","195/60R16 89H","205/55R16 91H","205/60R16 92H","205/65R16 95H","215/55R16 93V","215/60R16 95H","225/55R16 95W","225/60R16 98V","205/50R17 89H","205/55R17 91H","215/45R17 91W","215/50R17 95W","215/55R17 94V","215/60R17 96H","225/45R17 94W","225/50R17 98W","225/55R17 97V","235/45R17 97W","225/50R18 95V","225/55R18 98V",
        ],
        "keywords": [
            "Assurance TripleMax 2",
            "not Assurance TripleMax",
            "HydroTred technology",
            "175/65R14 82H",
            "205/55R16 91H",
            "225/50R18 95V",
            "shorter wet braking",
            "wet braking",
            "sizes",
            "passenger tire",
        ],
        "boundary_note": (
            "This parent segment belongs only to Assurance TripleMax 2. "
            "Do not use this segment for Assurance TripleMax."
        ),
        "guardrail_prefix": (
            "INDEXING GUARDRAIL: This segment is only for Assurance TripleMax 2. "
            "It must not be used for Assurance TripleMax."
        ),
    },
    37: {
        "product_name": "Assurance TripleMax 2",
        "category": "Passenger",
        "target_audience": "Drivers seeking safer wet braking and more comfortable driving",
        "features": [
            "Asymmetrical tread design for shorter wet braking performance.",
            "Squarish footprint for improved handling and steering precision.",
            "Optimized tread pattern to reduce noise for a more comfortable ride.",
        ],
        "performance_charts": [
            "Superior wet braking performance with innovative HydroTred technology.",
        ],
        "technology_descriptions": [
            "HydroTred technology improves wet-road braking performance.",
            "Asymmetric tread design supports handling and comfort performance.",
        ],
        "sizes": [
            "175/65R14 82H","175/65R14 82T","175/70R14 84H","185/60R14 82H","185/65R14 86H","195/60R14 86H","195/65R14 89H","175/65R15 84T","185/55R15 82V","185/60R15 84H","185/65R15 88H","195/50R15 82V","195/55R15 85V","195/60R15 88H","195/65R15 91H","205/65R15 94V","185/55R16 83V","185/60R16 86H","195/50R16 84V","195/55R16 87H","195/60R16 89H","205/55R16 91H","205/60R16 92H","205/65R16 95H","215/55R16 93V","215/60R16 95H","225/55R16 95W","225/60R16 98V","205/50R17 89H","205/55R17 91H","215/45R17 91W","215/50R17 95W","215/55R17 94V","215/60R17 96H","225/45R17 94W","225/50R17 98W","225/55R17 97V","235/45R17 97W","225/50R18 95V","225/55R18 98V",
        ],
        "keywords": [
            "Assurance TripleMax 2",
            "not Assurance TripleMax",
            "HydroTred technology",
            "wet braking",
            "175/65R14 82H",
            "205/55R16 91H",
            "215/60R17 96H",
            "225/50R18 95V",
            "handling performance",
            "quiet performance",
        ],
        "boundary_note": (
            "This parent segment belongs only to Assurance TripleMax 2. "
            "Its sizes and HydroTred content must not be mixed with Assurance TripleMax."
        ),
        "guardrail_prefix": (
            "INDEXING GUARDRAIL: This segment is only for Assurance TripleMax 2. "
            "It must not be used for Assurance TripleMax."
        ),
    },
    18: {
        "product_name": "Eagle F1 Asymmetric 6",
        "category": "Ultra High Performance Tire",
        "target_audience": "Sport Performance Enthusiasts",
        "features": [
            "Wet Braking Pro Technology for outstanding wet braking performance.",
            "Dry Contact Plus Technology for superior handling performance.",
            "Radial chamfered grooves for a quieter ride.",
        ],
        "performance_charts": [
            "Internal test with Volkswagen Golf 8, tire size 225/45R17, at Goodyear Proving Ground, Mireval, France.",
            "Wet handling and braking: 2% better than main competitor 1.",
            "Dry braking: 5% better than main competitor 2.",
        ],
        "technology_descriptions": [
            "Wet Braking Pro Technology uses new resin to create more micro-contact for wet braking.",
            "Dry Contact Plus Technology adapts the contact patch to driving style and road surface.",
            "Radial chamfered grooves reduce noise for quieter performance.",
        ],
        "sizes": [
            "195/55R15 85W","195/65R15 91V","195/50R16 84V","205/45R16 87W","205/50R16 91W","205/55R16 91W","205/60R16 92V","215/45R16 90W","215/60R16 95V","225/55R16 95W","205/40R17 84W","205/45R17 88Y","205/45R17 88W","205/50R17 93Y","215/40R17 87Y","215/45R17 87Y","215/45R17 91Y","215/50R17 91W","215/55R17 94V","225/45R17 94W","225/45R17 94Y","225/50R17 98Y","225/50R17 98W","225/55R17 97Y","225/55R17 101W","235/45R17 97Y","235/45R17 94W","245/40R17 95Y","245/40R17 95W","245/45R17 99Y","245/45R17 95Y","255/40R17 98W","215/40R18 89W","215/45R18 93W","225/40R18 92Y","225/45R18 95Y","225/45R18 95W","235/40R18 95W","235/40R18 95Y","235/45R18 98Y","235/45R18 98W","235/50R18 101Y","245/35R18 92Y","245/40R18 93Y","245/40R18 97Y","245/45R18 100Y","245/45R18 100W","255/35R18 94W","255/35R18 94Y","255/45R18 103Y","255/55R18 109Y","265/35R18 97Y","265/35R18 97W","225/35R19 88Y","225/45R19 96W","235/35R19 91Y","235/40R19 96Y","245/35R19 93Y","245/40R19 98Y","245/40R19 94V","245/45R19 102Y","245/50R19 105Y","255/35R19 96Y","255/40R19 100Y","255/50R19 107Y","275/35R19 100Y","285/30R19 98Y","245/40R20 99V","255/40R20 97V","255/45R20 105V","245/45R21 104V","275/40R21 107V",
        ],
        "keywords": [
            "Eagle F1 Asymmetric 6",
            "not Asymmetric 3",
            "not Asymmetric 5",
            "Wet Braking Pro Technology",
            "Dry Contact Plus Technology",
            "245/45R18 100W",
            "225/45R17 94W",
            "Mireval",
            "wet handling",
            "dry braking",
        ],
        "boundary_note": (
            "This parent segment belongs only to Eagle F1 Asymmetric 6. "
            "Use only these listed Asymmetric 6 sizes and do not mix with Eagle F1 Asymmetric 3 or Eagle F1 Asymmetric 5."
        ),
        "guardrail_prefix": (
            "INDEXING GUARDRAIL: This segment is only for Eagle F1 Asymmetric 6. "
            "It must not be used for Eagle F1 Asymmetric 3 or Eagle F1 Asymmetric 5."
        ),
    },
    22: {
        "product_name": "Eagle F1 Asymmetric 3",
        "category": "Ultra High Performance",
        "target_audience": "Sport performance enthusiasts",
        "features": [
            "Outstanding grip and responsive handling on wet and dry roads.",
            "Built with adhesive resin for better grip and braking performance.",
            "Increased surface contact area for shorter braking distance.",
            "Stronger lightweight construction for improved handling, cornering, tread wear, and fuel efficiency.",
        ],
        "performance_charts": [
            "Rolling resistance benchmark: Goodyear Eagle F1 Asymmetric 3 scored 100 versus 89.1 average for leading competitors.",
        ],
        "technology_descriptions": [
            "Adhesive resin increases stickiness with the road surface.",
            "Stronger lightweight construction improves handling and fuel efficiency.",
        ],
        "sizes": [
            "195/55R15 85W",
            "195/65R15 91V",
            "195/50R16 84V",
            "205/45R16 87W",
            "205/50R16 91W",
            "205/55R16 91W",
            "205/60R16 92V",
            "215/45R16 90W",
            "215/60R16 95V",
            "225/55R16 95W",
            "205/45R17 88W",
            "215/45R17 91Y",
            "215/50R17 91W",
            "215/55R17 94V",
            "225/45R17 91W",
            "225/45R17 94Y",
            "225/50R17 98Y",
            "235/45R17 94W",
            "245/40R17 95W",
            "245/45R17 95Y",
            "255/40R17 98W",
            "205/40R18 86W",
            "205/45R18 90V",
            "215/40R18 89W",
            "215/45R18 93W",
            "225/40R18 92Y",
            "225/45R18 91Y",
            "225/50R18 95W",
            "235/40R18 95W",
            "235/45R18 98W",
            "245/40R18 93Y",
            "245/45R18 100Y",
            "255/35R18 94W",
            "255/40R18 95Y",
            "255/55R18 109Y",
            "265/35R18 97W",
            "275/40R18 99Y",
            "225/40R19 93Y",
            "245/35R19 93Y",
            "245/40R19 98Y",
            "245/45R19 102Y",
            "255/35R19 96Y",
            "255/45R19 104Y",
            "265/45ZR19 105Y",
            "275/35R19 100Y",
            "275/40ZR19 105Y",
            "295/40ZR19 108Y",
            "225/40R20 94Y",
            "245/35R20 95Y",
            "255/35R20 97Y",
            "255/40R20 101Y",
            "265/40R20 104Y",
            "275/30R20 97Y",
            "275/35ZR20 98Y",
            "265/35ZR21 101Y",
            "305/30ZR21 104Y",
            "265/35R22 102W",
            "285/35R22 106W",
        ],
        "keywords": [
            "Eagle F1 Asymmetric 3",
            "not SUV",
            "Ultra High Performance",
            "adhesive resin",
            "195/55R15 85W",
            "225/45R17 91W",
            "245/40R19 98Y",
            "265/35ZR21 101Y",
            "rolling resistance",
            "TUV",
        ],
        "boundary_note": (
            "This parent segment belongs only to Eagle F1 Asymmetric 3 passenger fitments. "
            "Do not use this segment for Eagle F1 Asymmetric 3 SUV, Eagle F1 Asymmetric 5, or Eagle F1 Asymmetric 6."
        ),
        "guardrail_prefix": (
            "INDEXING GUARDRAIL: This segment is only for Eagle F1 Asymmetric 3 passenger sizes. "
            "It must not be used for Eagle F1 Asymmetric 3 SUV."
        ),
    },
    27: {
        "product_name": "Eagle F1 Asymmetric 3 SUV",
        "category": "Sport Performance",
        "target_audience": "SUV owners",
        "features": [
            "Shorter braking distances on wet and dry roads",
            "Improved SUV handling",
            "Superior cornering and wet braking performance",
        ],
        "performance_charts": [],
        "technology_descriptions": [
            "Unique compound provides better grip through optimal stability construction.",
            "Designed with three key technologies for shorter braking distance, outstanding handling performance, and excellent fuel efficiency.",
        ],
        "sizes": [
            "235/55R19 101Y",
            "255/50R19 103Y",
            "255/55R19 107W",
            "255/55R19 111W",
            "255/55R19 111Y",
            "265/50R19 110Y",
            "265/45R20 108Y",
            "285/45R20 108W",
            "285/45R20 112Y",
            "285/40R21 109Y",
        ],
        "keywords": [
            "Eagle F1 Asymmetric 3 SUV",
            "SUV",
            "sport performance",
            "wet braking",
            "cornering performance",
            "235/55R19 101Y",
            "255/50R19 103Y",
            "265/50R19 110Y",
            "265/45R20 108Y",
            "285/40R21 109Y",
        ],
        "boundary_note": (
            "This parent segment is curated only for Eagle F1 Asymmetric 3 SUV. "
            "The second AVAILABLE SIZES table in the raw OCR belongs to Eagle F1 Asymmetric 2 SUV and must not be used for Eagle F1 Asymmetric 3 SUV."
        ),
        "guardrail_prefix": (
            "INDEXING GUARDRAIL: This segment is only for Eagle F1 Asymmetric 3 SUV. "
            "It must not be used for Eagle F1 Asymmetric 3 passenger fitments or Eagle F1 Asymmetric 2 SUV."
        ),
    },
    39: {
        "product_name": "Assurance TripleMax",
        "category": "Passenger",
        "target_audience": "",
        "features": [
            "Durability Performance",
            "Wet Performance",
        ],
        "performance_charts": [],
        "technology_descriptions": [
            "Functionalized Polymer Tread Compound with improved molecular bonding provides outstanding grip.",
            "Wide Face Cavity provides better control during braking through optimized pressure distribution.",
            "Biting Edges increase contact area for extra braking security.",
        ],
        "sizes": [
            "165/70R14 81T",
            "185/70R14 88H",
            "175/60R15 81H",
            "175/60R15 81T",
            "175/65R15 84T",
            "185/55R15 82V",
            "185/60R15 84H",
            "185/65R15 88H",
            "195/50R15 82V",
            "195/55R15 85V",
            "195/60R15 88V",
            "195/65R15 91H",
            "195/65R15 91V",
            "205/65R15 94V",
            "185/55R16 83V",
            "195/55R16 87H",
            "195/55R16 87V",
            "195/60R16 89H",
            "205/55R16 91V",
            "205/60R16 92V",
            "205/65R16 95H",
            "205/65R16 95V",
            "215/60R16 95V",
            "205/50R17 89W",
            "215/45R17 87W",
            "215/50R17 91V",
            "215/55R17 94V",
            "215/60R17 96H",
            "225/45R17 94W",
            "225/55R17 97V",
        ],
        "keywords": [
            "Assurance TripleMax",
            "not TripleMax 2",
            "Functionalized Polymer",
            "Wide Face Cavity",
            "Biting Edges",
            "165/70R14 81T",
            "205/55R16 91V",
            "205/65R16 95V",
            "215/60R17 96H",
            "225/55R17 97V",
        ],
        "boundary_note": (
            "This parent segment belongs only to Assurance TripleMax. "
            "Do not mix with Assurance TripleMax 2 or any OEM fitment tables."
        ),
        "guardrail_prefix": (
            "INDEXING GUARDRAIL: This segment is only for Assurance TripleMax. "
            "It must not be used for Assurance TripleMax 2."
        ),
    },
    20: {
        "product_name": "Eagle F1 Asymmetric 5",
        "category": "Sport Performance",
        "target_audience": "",
        "features": [
            "Superior braking performance on wet and dry roads.",
            "Highly refined compound for shorter braking distance.",
            "ActiveBraking Technology for increased surface contact during braking.",
            "Tire construction and tread pattern designed for excellent dry handling.",
        ],
        "performance_charts": [
            "Wet braking improved by 4% versus Eagle F1 Asymmetric 3.",
            "Dry handling improved by 7% versus Eagle F1 Asymmetric 3.",
            "Internal test based on 225/45R17 91Y, Golf 7 GTi, at Goodyear Proving Ground.",
        ],
        "technology_descriptions": [
            "Highly refined compound delivers shorter braking distance on wet and dry roads.",
            "ActiveBraking Technology increases surface contact area when braking.",
        ],
        "sizes": [
            "195/55R15 85W","195/65R15 91V","195/50R16 84V","205/45R16 87W","205/50R16 91W","205/55R16 91W","205/60R16 92V","215/45R16 90W","215/60R16 95V","225/55R16 95W","205/45R17 88W","205/45R17 88Y","205/50R17 93Y","215/40R17 87Y","215/45R17 91Y","215/50R17 91W","215/55R17 94V","225/45R17 91Y","225/45R17 94W","225/45R17 94Y","225/50R17 94Y","225/50R17 98W","225/50R17 98Y","225/55R17 101W","225/55R17 97Y","235/45R17 94W","235/45R17 97Y","235/55R17 103Y","245/40R17 91Y","245/40R17 95W","245/40R17 95Y","245/45R17 95Y","245/45R17 99Y","255/40R17 98W","215/40R18 89W","215/45R18 93W","225/35R18 87W","225/40R18 92Y","225/45R18 95W","225/45R18 95Y","225/50R18 95W","235/40R18 95W","235/40R18 95Y","235/45R18 98W","235/45R18 98Y","235/50R18 101Y","245/35R18 92Y","245/40R18 93Y","245/40R18 97Y","245/45R18 100W","245/45R18 100Y","255/35R18 94W","255/40R18 99Y","255/45R18 103Y","255/55R18 109W","255/55R18 109Y","265/35R18 97W","265/35R18 97Y","275/35R18 99Y","225/35R19 88Y","225/40R19 93Y","225/45R19 96W","235/35R19 91Y","235/40R19 96Y","235/55R19 105H","235/55R19 105W","245/35R19 93Y","245/40R19 98Y","245/45R19 102Y","255/30R19 91Y","255/35R19 96Y","255/40R19 100Y","255/45R19 104Y","255/50R19 107Y","275/35R19 100Y","285/30R19 98Y","235/50R20 104W","245/35R20 95Y","255/35R20 97Y","255/40R20 101Y","255/45R20 105H","255/45R20 105W","265/30R20 94Y","265/35R20 99Y","275/30R20 97Y","285/30R20 99Y","295/35R20 105Y","245/30R21 91Y","245/45R21 104W","265/35R21 101Y","265/40R21 105H","265/40R21 105Y","285/35R21 105Y","305/30R21 104Y",
        ],
        "keywords": [
            "Eagle F1 Asymmetric 5",
            "not Asymmetric 3",
            "not Asymmetric 6",
            "ActiveBraking Technology",
            "225/45R17 91Y",
            "245/45R18 100W",
            "255/45R20 105W",
            "265/40R21 105Y",
            "wet braking",
            "dry handling",
        ],
        "boundary_note": (
            "This parent segment belongs only to Eagle F1 Asymmetric 5. "
            "Do not mix with Eagle F1 Asymmetric 3 or Eagle F1 Asymmetric 6."
        ),
        "guardrail_prefix": (
            "INDEXING GUARDRAIL: This segment is only for Eagle F1 Asymmetric 5. "
            "It must not be used for Eagle F1 Asymmetric 3 or Eagle F1 Asymmetric 6."
        ),
    },
    42: {
        "product_name": "Assurance ComfortTred",
        "category": "Passenger",
        "target_audience": "Luxurious vehicles",
        "features": [
            "Quiet ride",
            "Comfortable ride",
            "ANX Technology with noise canceling layer",
            "Cushioning layer to reduce vibration",
        ],
        "performance_charts": [
            "Wet braking test on 40% low Mu asphalt, 40% high Mu asphalt, and 20% concrete.",
            "Test size 245/45R18 on AUDI A6.",
            "Test locations MIREVAL(FR) and ZHAOYUAN(CN), May 2022.",
            "Ranked #1 in subjective noise.",
            "Ranked #1 in ride comfort.",
            "Ranked #1 in pass-by noise.",
        ],
        "technology_descriptions": [
            "ANX Technology uses a noise canceling layer to suppress rolling noise.",
            "Cushioning layer reduces vibration for a more comfortable ride.",
        ],
        "sizes": [
            "195/60R16 93H","205/55R16 91W","205/60R16 92W","215/55R16 97W","215/60R16 95W","225/55R16 95Y","205/50R17 93H","205/55R17 95H","215/50R17 95W","215/55R17 94V","215/55R17 98W","225/45R17 94Y","225/50R17 98Y","225/55R17 97Y","225/60R17 103W","235/45R17 94W","235/50R17 96W","235/55R17 103W","245/45R17 99Y","225/40R18 92V","225/45R18 95W","225/60R18 100H","235/45R18 98W","235/50R18 97W","245/40R18 93W","245/40R18 93Y","245/40R18 97Y","245/45R18 100W","245/45R18 100Y","245/45R18 96V","225/40R19 93V","245/45R19 102V","245/45R19 102W","225/45R21 99W",
        ],
        "keywords": [
            "Assurance ComfortTred",
            "ANX Technology",
            "quiet ride",
            "comfortable ride",
            "215/55R17 98W",
            "245/40R18 97Y",
            "245/45R18",
            "AUDI A6",
            "MIREVAL",
            "pass-by noise",
        ],
        "boundary_note": "This parent segment belongs only to Assurance ComfortTred.",
    },
    63: {
        "product_name": "Wrangler AT SilentTrac",
        "category": "All Terrain",
        "target_audience": "SUV / 4X4",
        "features": [
            "DuraWall Technology for resistance against cuts and punctures",
            "Thicker rubber under tread for vibration absorption",
            "Angled block tread design for quiet performance",
            "Optimized cavity shape for superior mileage",
        ],
        "performance_charts": [
            "Off Road Handling 4WD",
            "ECE Noise",
            "Off Road Gravel Handling 4WD",
            "Interior Noise Subjective",
            "Comfort",
            "Wet Braking",
            "Wet Handling",
            "Dry Braking",
            "Ride and Handling overall",
            "Off Road Dirt straight-line acceleration",
        ],
        "technology_descriptions": [
            "DuraWall Technology provides greater resistance against cuts and punctures for off-road terrains.",
            "Thicker rubber under tread absorbs vibration and supports quiet performance.",
            "Optimized cavity shape increases wearable volume for mileage.",
        ],
        "sizes": [
            "215/75R15 100S","225/70R15 100S","225/75R15 102T","235/70R15 103T","235/75R15 109T","215/65R16 98H","235/70R16 106T","245/70R16 111T","255/70R16 111H","265/70R16 112H","265/70R16 116H","LT225/75R16 115/112","LT245/75R16 120/116S","LT265/75R16 123/120Q","LT285/75R16 126/123Q","225/60R17 99H","225/65R17 102T","235/65R17 104H","255/65R17 110T","265/65R17 112H","265/65R17 112S","265/70R17 116H","275/65R17 115T","LT285/65R17 121/118S","265/60R18 110H","LT285/60R18 122/119S","225/75R15C 110/108S","255/70R15C 112/110Q","255/70R15C 112/110S","30X9.50R15LT 104","31X10.50R15LT 109","205R16LT 112/110T","225/70R17C 112/110S",
        ],
        "keywords": [
            "Wrangler AT SilentTrac",
            "DuraWall Technology",
            "All Terrain",
            "255/70R15C 112/110S",
            "255/70R15C 112/110Q",
            "225/70R17C 112/110S",
            "off road",
            "quiet performance",
            "mileage performance",
            "SUV 4X4",
        ],
        "boundary_note": "This parent segment belongs only to Wrangler AT SilentTrac.",
    },
    38: {
        "product_name": "Assurance TripleMax",
        "category": "Passenger",
        "target_audience": "",
        "features": [
            "Outstanding wet grip performance on wet roads",
            "Functionalized Polymer Tread Compound supports grip.",
            "Wide Face Cavity improves braking control.",
            "Biting Edges increase braking security.",
        ],
        "performance_charts": [
            "Wet-road braking distance test from 80 km/h to 20 km/h.",
            "Measured by TUV SUD Automotive in November 2012.",
            "Test tire size: 205/55R16 91V.",
            "Test car: Toyota Auris.",
            "Test location: FAKT Memmingen, Germany.",
            "Reference report number: 76250397.",
        ],
        "technology_descriptions": [
            "Functionalized Polymer Tread Compound provides improved molecular bonding for grip.",
            "Wide Face Cavity increases contact area and optimizes pressure distribution for braking control.",
            "Biting Edges provide extra contact area for braking security.",
        ],
        "sizes": [],
        "keywords": [
            "Assurance TripleMax",
            "Functionalized Polymer Tread Compound",
            "Wide Face Cavity",
            "Biting Edges",
            "wet grip performance",
            "wet-road braking test",
            "205/55R16 91V",
            "report 76250397",
        ],
        "boundary_note": (
            "This parent segment is the Assurance TripleMax wet-braking proof point and technology summary. "
            "Use it for Assurance TripleMax performance-chart and technology answers, not for Assurance TripleMax 2."
        ),
        "guardrail_prefix": (
            "INDEXING GUARDRAIL: This segment is only for Assurance TripleMax. "
            "It must not be used for Assurance TripleMax 2."
        ),
    },
}


def normalize_api_endpoint(raw_endpoint: str) -> str:
    endpoint = raw_endpoint.strip().rstrip("/")
    if "localhost" in endpoint or "127.0.0.1" in endpoint:
        try:
            response = requests.get(f"{endpoint}/info", timeout=3)
            if response.ok or response.status_code in {401, 404}:
                return endpoint
        except requests.RequestException:
            return LOCAL_DIFY_FALLBACK
    return endpoint


def extract_raw_content(content: str) -> str:
    match = re.search(
        rf"{re.escape(RAW_HEADER)}\s*(.*?)\s*---\s*{re.escape(AI_HEADER)}",
        content,
        flags=re.DOTALL,
    )
    return match.group(1).strip() if match else content.strip()


def build_hybrid_content(raw_content: str, fix: dict[str, Any]) -> str:
    lines = []
    if fix.get("guardrail_prefix"):
        lines.append(fix["guardrail_prefix"])
        lines.append("")
    lines.extend([RAW_HEADER, raw_content, "---", AI_HEADER])
    lines.append(f"**Product:** {fix['product_name']}")
    if fix.get("category"):
        lines.append(f"**Category:** {fix['category']}")
    if fix.get("target_audience"):
        lines.append(f"**Target Audience:** {fix['target_audience']}")

    lines.append("")
    lines.append("**Product Features:**")
    if fix["features"]:
        lines.extend(f"- {item}" for item in fix["features"])
    else:
        lines.append("- Not identified in this parent segment")

    lines.append("")
    lines.append("**Performance Charts:**")
    if fix["performance_charts"]:
        lines.extend(f"- {item}" for item in fix["performance_charts"])
    else:
        lines.append("- Not identified in this parent segment")

    lines.append("")
    lines.append("**Technology Descriptions:**")
    if fix["technology_descriptions"]:
        lines.extend(f"- {item}" for item in fix["technology_descriptions"])
    else:
        lines.append("- Not identified in this parent segment")

    lines.append("")
    lines.append("**Available Sizes:**")
    if fix["sizes"]:
        lines.extend(f"- {item}" for item in fix["sizes"])
        lines.append("")
        lines.append(f"**Available Size Count:** {len(fix['sizes'])}")
    else:
        lines.append("- Not identified in this parent segment")

    if fix.get("boundary_note"):
        lines.append("")
        lines.append(f"**Product Boundary Note:** {fix['boundary_note']}")

    lines.append("")
    lines.append(f"**Keywords:** {', '.join(fix['keywords']) or 'None'}")
    return "\n".join(lines).strip() + "\n"


def fetch_segments(api_url: str, headers: dict[str, str]) -> list[dict[str, Any]]:
    response = requests.get(
        f"{api_url}/datasets/{DATASET_ID}/documents/{DOCUMENT_ID}/segments?page=1&limit=100",
        headers=headers,
        timeout=60,
    )
    response.raise_for_status()
    return response.json()["data"]


def update_segment(api_url: str, headers: dict[str, str], segment_id: str, content: str, keywords: list[str]) -> None:
    url = f"{api_url}/datasets/{DATASET_ID}/documents/{DOCUMENT_ID}/segments/{segment_id}"
    for payload in (
        {"segment": {"content": content, "answer": "", "regenerate_child_chunks": True}},
        {"segment": {"content": content, "answer": "", "keywords": keywords, "regenerate_child_chunks": True}},
    ):
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()


def main() -> None:
    env = dotenv_values(ENV_PATH)
    api_url = normalize_api_endpoint(env.get("API_ENDPOINT", "http://localhost/v1"))
    headers = {"Authorization": f"Bearer {env['DIFY_DATABASE_KEY']}", "Content-Type": "application/json"}
    segments = fetch_segments(api_url, headers)
    by_position = {segment["position"]: segment for segment in segments}

    for position, fix in FIXES.items():
        segment = by_position[position]
        raw_content = extract_raw_content(segment["content"])
        hybrid_content = build_hybrid_content(raw_content, fix)
        update_segment(api_url, headers, segment["id"], hybrid_content, fix["keywords"])
        print(f"updated position={position} segment={segment['id']}")


if __name__ == "__main__":
    main()
