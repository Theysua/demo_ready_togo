import re
import pprint

with open("Goodyear_Structured_Knowledge_Base.md", "r") as f:
    text = f.read()

products = text.split("---PRODUCT_BOUNDARY---")
header = products[0]

# user sizes for asymmetric 5
user_text = "195/55R15 85W195/65R15 91V195/50R16 84V205/45R16 87W205/50R16 91W205/50R16 91W205/55R16 91W205/60R16 92V215/45R16 90W215/60R16 95V225/55R16 95W205/45R17 88W205/45R17 88W205/45R17 88Y205/50R17 93Y215/40R17 87Y215/45R17 91Y215/45R17 91Y215/50R17 91W215/55R17 94V225/45R17 91Y225/45R17 91Y225/45R17 91Y225/45R17 94W225/45R17 94Y225/50R17 94Y225/50R17 94Y225/50R17 98W225/50R17 98Y225/55R17 101W225/55R17 101W225/55R17 97Y235/45R17 94W235/45R17 97Y235/55R17 103Y245/40R17 91Y245/40R17 95W245/40R17 95Y245/45R17 95Y245/45R17 95Y245/45R17 99Y245/45R17 99Y245/45R17 99Y255/40R17 98W215/40R18 89W215/45R18 93W215/45R18 93W225/35R18 87W225/40R18 92Y225/40R18 92Y225/40R18 92Y225/40R18 92Y225/40R18 92Y225/45R18 95W225/45R18 95Y225/45R18 95Y225/45R18 95Y225/45R18 95Y225/45R18 95Y225/45R18 95Y225/50R18 95W235/40R18 95W235/40R18 95W235/40R18 95Y235/45R18 98W235/45R18 98W235/45R18 98Y235/50R18 101Y245/35R18 92Y245/40R18 93Y245/40R18 93Y245/40R18 97Y245/40R18 97Y245/45R18 100W245/45R18 100Y255/35R18 94W255/40R18 99Y255/40R18 99Y255/40R18 99Y255/40R18 99Y255/40R18 99Y255/45R18 103Y255/55R18 109W255/55R18 109Y265/35R18 97W265/35R18 97Y275/35R18 99Y225/35R19 88Y225/40R19 93Y225/40R19 93Y225/45R19 96W235/35R19 91Y235/40R19 96Y235/55R19 105H235/55R19 105W245/35R19 93Y245/35R19 93Y245/40R19 98Y245/40R19 98Y245/45R19 102Y245/45R19 102Y245/45R19 102Y245/45R19 102Y255/30R19 91Y255/35R19 96Y255/35R19 96Y255/40R19 100Y255/45R19 104Y255/50R19 107Y255/50R19 107Y275/35R19 100Y285/30R19 98Y235/50R20 104W245/35R20 95Y245/35R20 95Y255/35R20 97Y255/40R20 101Y255/40R20 101Y255/40R20 101Y255/40R20 101Y255/40R20 101Y255/40R20 101Y255/45R20 105H255/45R20 105H255/45R20 105W265/30R20 94Y265/35R20 99Y275/30R20 97Y285/30R20 99Y295/35R20 105Y245/30R21 91Y245/45R21 104W265/35R21 101Y265/40R21 105H265/40R21 105Y285/35R21 105Y305/30R21 104Y"
asym5_matches = re.finditer(r'(\d{3}/\d{2}R\d{2}\s?\d{2,3}[A-Z])', user_text)
asym5_unique = []
seen = set()
for m in asym5_matches:
    s = m.group(1).strip()
    if s not in seen:
        seen.add(s)
        asym5_unique.append(f"- {s}")

# Dict to hold merged data
# "NAME": { "features": [], "techs": [], "charts": [], "sizes": [] }
kb = {}

for p in products[1:]:
    # Extract sections
    name_match = re.search(r'Product Name:\s*\*\*(.*?)\*\*', p)
    if not name_match: continue
    
    name_raw = name_match.group(1).strip()
    name = name_raw.upper()
    
    if name not in kb:
        kb[name] = {"features": [], "techs": [], "charts": [], "sizes": [], "raw_name": name_raw}
        
    feat_match = re.search(r'\[Product Features\](.*?)(\n\[|$)', p, re.DOTALL)
    if feat_match:
        lines = [x.strip() for x in feat_match.group(1).strip().split('\n') if x.strip().startswith('-')]
        for l in lines:
            if l not in kb[name]["features"]: kb[name]["features"].append(l)

    tech_match = re.search(r'\[Technology Descriptions\](.*?)(\n\[|$)', p, re.DOTALL)
    if tech_match:
        lines = [x.strip() for x in tech_match.group(1).strip().split('\n') if x.strip().startswith('-')]
        for l in lines:
            if l not in kb[name]["techs"]: kb[name]["techs"].append(l)

    chart_match = re.search(r'\[Performance Charts\](.*?)(\n\[|$)', p, re.DOTALL)
    if chart_match:
        chart_text = chart_match.group(1).strip()
        if chart_text and chart_text not in kb[name]["charts"]:
            kb[name]["charts"].append(chart_text)

    size_match = re.search(r'\[Available Sizes\](.*?)(\n\[|$)', p, re.DOTALL)
    if size_match:
        lines = size_match.group(1).strip().split('\n')
        for l in lines:
            # Maybe it's comma separated from dify merge or bulleted locally
            if not l.strip(): continue
            if l.startswith('-'): l = l.strip()[1:].strip()
            
            # Sub split by comma in case they were merged
            parts = [x.strip() for x in l.split(',') if x.strip()]
            for p_size in parts:
                formatted = f"- {p_size}"
                if formatted not in kb[name]["sizes"]:
                    kb[name]["sizes"].append(formatted)


# Replace Asymmetric 5 sizes
if "EAGLE F1 ASYMMETRIC 5" in kb:
    kb["EAGLE F1 ASYMMETRIC 5"]["sizes"] = asym5_unique

# Reconstruct the file
with open("Goodyear_Structured_Knowledge_Base_Merged.md", "w") as out:
    out.write(header.strip() + "\n\n")
    
    for name, data in kb.items():
        out.write(f"---PRODUCT_BOUNDARY---\n")
        out.write(f"Product Name: **{data['raw_name']}**\n\n")
        
        if data["features"]:
            out.write("[Product Features]\n")
            for f in data["features"]: out.write(f"{f}\n")
            out.write("\n")
            
        if data["techs"]:
            out.write("[Technology Descriptions]\n")
            for t in data["techs"]: out.write(f"{t}\n")
            out.write("\n")
            
        if data["charts"]:
            out.write("[Performance Charts]\n")
            for c in data["charts"]: out.write(f"{c}\n")
            out.write("\n")
            
        if data["sizes"]:
            out.write("[Available Sizes]\n")
            # We must output them comma-separated to keep them in one chunk without newlines!
            # Wait, our previous python merge made them comma separated on ONE line with a hyphen.
            clean_sizes = [s.replace('- ', '') for s in data["sizes"]]
            out.write("- " + ", ".join(clean_sizes) + "\n\n")
            
print(f"Merged {len(kb)} completely unified products. Wrote to Goodyear_Structured_Knowledge_Base_Merged.md")
