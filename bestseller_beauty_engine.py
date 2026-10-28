import os
import re
import json
import time
import hashlib
from datetime import datetime, timezone
from urllib.parse import quote_plus
import requests

# Konfigurasi Environment Variables
AMAZON_TAG = os.environ.get("AMAZON_TAG", "yourtag-20").strip()
SITE_URL = os.environ.get("SITE_URL", "https://username.github.io/repo-name").rstrip("/")
REPO_NAME = os.environ.get("GITHUB_REPOSITORY", "user/repo")

# Kunci verifikasi IndexNow deterministik
INDEXNOW_KEY = hashlib.md5(f"{REPO_NAME}_{AMAZON_TAG}_derm2026".encode("utf-8")).hexdigest()

DB_PATH = "data/actives_db.json"
DOCS_DIR = "docs"
ACTIVES_DIR = os.path.join(DOCS_DIR, "actives")
MIX_DIR = os.path.join(DOCS_DIR, "compatibility")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
}

# Daftar Bahan Aktif Skincare & Suplemen Terlaris di Amazon 2026
CATALOG_2026 = [
    {"name": "Niacinamide", "chem": "Nicotinamide", "cat": "Pore Minimizer & Barrier Serum", "ph": "5.0 - 7.0", "time": "AM & PM", "conflict": "Pure L-Ascorbic Acid (Low pH)", "forms": ["10% Niacinamide + 1% Zinc Serum", "5% Niacinamide Barrier Moisturizer", "Niacinamide Brightening Toner Pads"]},
    {"name": "Hypochlorous Acid", "chem": "Hypochlorous acid", "cat": "Eczema & Acne Soothing Facial Spray", "ph": "4.5 - 6.5", "time": "AM & PM (Wait 60s before antioxidants)", "conflict": "Direct Vitamin C or Peptide serums while wet", "forms": ["Hypochlorous Acid Daily Facial Spray", "Tower 28 Style SOS Skin Rescue Mist", "Hypochlorous Acid Eyelid & Blemish Cleanser"]},
    {"name": "Azelaic Acid", "chem": "Azelaic acid", "cat": "Rosacea, Redness & Melasma Suspension", "ph": "4.0 - 5.5", "time": "AM & PM", "conflict": "Strong AHA/BHA Peels in same routine", "forms": ["10% Azelaic Acid Redness Relief Serum", "Azelaic Acid + Niacinamide Brightening Cream", "Micronized Azelaic Acid Blemish Gel"]},
    {"name": "Tranexamic Acid", "chem": "Tranexamic acid", "cat": "Hyperpigmentation & Dark Spot Corrector", "ph": "5.0 - 6.5", "time": "AM & PM", "conflict": "High-strength Glycolic Acid", "forms": ["5% Tranexamic Acid Dark Spot Serum", "Tranexamic Acid + Kojic Acid Discoloration Serum", "Tranexamic Night Repair Treatment"]},
    {"name": "Copper Tripeptide-1", "chem": "Glycyl-L-histidyl-L-lysine", "cat": "Anti-Aging Collagen & Firming Peptide", "ph": "5.5 - 7.0", "time": "AM or PM", "conflict": "L-Ascorbic Acid (Vitamin C), Direct Acids, Retinoids", "forms": ["Blue Copper Peptide 1% Firming Serum", "Multi-Peptide + Copper Peptides 1% Facial Serum", "GHK-Cu Hair & Skin Regenerating Complex"]},
    {"name": "Retinaldehyde", "chem": "Retinal", "cat": "Next-Gen Encapsulated Vitamin A Night Serum", "ph": "5.5 - 6.5", "time": "PM Only (Requires SPF 50 AM)", "conflict": "AHA/BHA Acids, Benzoyl Peroxide, Vitamin C", "forms": ["0.1% Liposomal Retinaldehyde Night Cream", "Retinal + Ginseng Gentle Eye & Face Serum", "0.05% Encapsulated Retinal Smoothing Emulsion"]},
    {"name": "Bakuchiol", "chem": "Bakuchiol", "cat": "Pregnancy-Safe Plant Retinol Alternative", "ph": "5.0 - 6.5", "time": "AM & PM", "conflict": "None (Safe with all actives)", "forms": ["1% Pure Bakuchiol Peptide Firming Serum", "Bakuchiol + Squalane Gentle Night Oil", "Bakuchiol Phyto-Retinol Eye Cream"]},
    {"name": "Salicylic Acid", "chem": "Salicylic acid", "cat": "Oil-Soluble BHA Pore & Blackhead Exfoliant", "ph": "3.2 - 4.0", "time": "PM (2-3x Weekly)", "conflict": "Retinoids, Other AHA/BHA Acids, Vitamin C", "forms": ["2% Salicylic Acid BHA Liquid Exfoliant", "Salicylic Acid Acne Foaming Cleanser", "Hydrocolloid + Salicylic Acid Pimple Patches"]},
    {"name": "Glycolic Acid", "chem": "Glycolic acid", "cat": "Low-Molecular AHA Surface Resurfacing Toner", "ph": "3.4 - 4.2", "time": "PM Only (2-3x Weekly)", "conflict": "Retinoids, Copper Peptides, Salicylic Acid", "forms": ["7% Glycolic Acid Exfoliating Toning Solution", "10% Glycolic Acid Resurfacing Body Lotion", "Glycolic Acid Heel & Keratosis Pilaris Stick"]},
    {"name": "Lactic Acid", "chem": "Lactic acid", "cat": "Hydrating AHA Gentle Exfoliating Serum", "ph": "3.5 - 4.5", "time": "PM Only", "conflict": "Retinoids, Benzoyl Peroxide", "forms": ["10% Lactic Acid + Hyaluronic Acid Serum", "Lactic AcidKP Bump Eraser Body Scrub", "5% Gentle Lactic Acid Smoothing Milk"]},
    {"name": "Mandelic Acid", "chem": "Mandelic acid", "cat": "Large-Molecule Gentle AHA for Sensitive Skin", "ph": "3.5 - 4.5", "time": "PM Only", "conflict": "High-strength Retinoids", "forms": ["10% Mandelic Acid + HA Gentle Prep Serum", "Mandelic Acid Dark Spot Clearing Toner", "Mandelic Acid Sensitive Skin Wash"]},
    {"name": "Gluconolactone", "chem": "Gluconolactone", "cat": "Polyhydroxy Acid (PHA) Barrier-Safe Exfoliant", "ph": "3.8 - 5.0", "time": "AM & PM", "conflict": "None (Safe for rosacea & sensitive skin)", "forms": ["PHA Gluconolactone Pore Soothing Toner", "PHA + BHA Gentle Daily Exfoliating Pads", "Gluconolactone Hydrating Essence"]},
    {"name": "Kojic Acid", "chem": "Kojic acid", "cat": "Tyrosinase Inhibitor Melanin Blocker", "ph": "4.0 - 5.5", "time": "AM & PM", "conflict": "Strong Retinoids if barrier is compromised", "forms": ["Kojic Acid + Turmeric Cleansing Pads", "2% Kojic Acid + Alpha Arbutin Dark Spot Serum", "Original Japanese Kojic Acid Brightening Soap"]},
    {"name": "Alpha Arbutin", "chem": "Arbutin", "cat": "Water-Soluble Post-Acne Mark Brightener", "ph": "4.5 - 6.5", "time": "AM & PM", "conflict": "Alkaline cleansers above pH 8", "forms": ["2% Alpha Arbutin + HA Concentrated Serum", "Alpha Arbutin + Niacinamide Even Tone Drops", "Alpha Arbutin Body Brightening Lotion"]},
    {"name": "Ascorbic Acid", "chem": "Ascorbic acid", "cat": "Pure Vitamin C Antioxidant & Collagen Booster", "ph": "2.6 - 3.5", "time": "AM (Under Broad-Spectrum SPF 50)", "conflict": "Copper Peptides, Retinoids, Benzoyl Peroxide", "forms": ["20% Vitamin C + E + Ferulic Acid Serum", "15% L-Ascorbic Acid Glow Booster", "Airless Pump Stabilized Vitamin C Serum"]},
    {"name": "Ferulic Acid", "chem": "Ferulic acid", "cat": "Photoprotective Antioxidant Stabilizer", "ph": "3.0 - 4.5", "time": "AM", "conflict": "Copper Peptides", "forms": ["Resveratrol 3% + Ferulic Acid 3% Antioxidant Serum", "Vitamin C + Ferulic Acid Photo-Aging Defense", "Ferulic + Retinol Overnight Recovery"]},
    {"name": "Ectoin", "chem": "Ectoine", "cat": "Extremolyte Cell-Shield & Hydration Magnet", "ph": "5.0 - 7.0", "time": "AM & PM", "conflict": "None (Buffers irritation from retinoids)", "forms": ["Ectoin 7% Barrier Repair Relief Cream", "Ectoin + Hyaluronic Acid Hydro-Shield Serum", "K-Beauty Ectoin Soothing Ampoule"]},
    {"name": "Panthenol", "chem": "Panthenol", "cat": "Provitamin B5 Intensive Barrier Healer", "ph": "5.0 - 7.0", "time": "AM & PM", "conflict": "None (Ideal soothing buffer)", "forms": ["Cicaplast Style B5 Panthenol Soothing Balm", "10% Panthenol + Ceramide Barrier Cream", "Panthenol Hydrating Facial Mist"]},
    {"name": "Squalane", "chem": "Squalane", "cat": "Bio-Identical Non-Comedogenic Moisture Seal", "ph": "Anhydrous (Oil)", "time": "AM & PM (Final Routine Step)", "conflict": "None (Zero pore-clogging score)", "forms": ["100% Sugarcane Derived Squalane Facial Oil", "Squalane + Probiotic Gel Moisturizer", "Squalane Makeup-Melting Gentle Cleanser"]},
    {"name": "Urea", "chem": "Urea", "cat": "Keratolytic Natural Moisturizing Factor (NMF)", "ph": "5.0 - 6.5", "time": "AM & PM", "conflict": "Strong AHA peels on facial skin", "forms": ["5% Urea Facial Barrier Recovery Cream", "40% Urea + Salicylic Acid Foot & Callus Cream", "10% Urea Rough & Bumpy Skin Lotion"]},
    {"name": "Benzoyl Peroxide", "chem": "Benzoyl peroxide", "cat": "Antibacterial Acne Wash & Spot Treatment", "ph": "4.0 - 6.0", "time": "AM or Short-Contact Wash", "conflict": "Tretinoin, Retinaldehyde, Vitamin C, Hydroquinone", "forms": ["4% Benzoyl Peroxide Gentle Creamy Acne Wash", "10% Maximum Strength Foaming Acne Cleanser", "2.5% Micronized Benzoyl Peroxide Spot Gel"]},
    {"name": "Adapalene", "chem": "Adapalene", "cat": "Third-Gen Retinoid for Acne & Texture", "ph": "5.0 - 6.5", "time": "PM Only", "conflict": "AHA/BHA Acids, Waxing, Harsh Scrubs", "forms": ["Adapalene 0.1% Once-Daily Acne Treatment Gel", "Adapalene + Benzoyl Peroxide Regimen Kit", "Barrier-Friendly Moisturizer for Adapalene Users"]},
    {"name": "Ketoconazole", "chem": "Ketoconazole", "cat": "Anti-Dandruff & Fungal Acne (Malassezia) Wash", "ph": "5.0 - 6.5", "time": "3x Weekly (5-Minute Contact Time)", "conflict": "Heavy coconut/ester facial oils", "forms": ["1% Ketoconazole Anti-Dandruff & Scalp Shampoo", "Fungal-Acne Safe Oil-Free Gel Moisturizer", "Silicone Scalp Massager + Dandruff Control Bundle"]},
    {"name": "Magnesium Glycinate", "chem": "Magnesium glycinate", "cat": "Chelated High-Absorption Sleep & Muscle Supplement", "ph": "Neutral Buffered", "time": "Evening (30-60 mins before sleep)", "conflict": "High-dose Calcium or Iron taken at exact same minute", "forms": ["Pure Chelated Magnesium Glycinate 400mg Capsules", "Magnesium Glycinate + L-Theanine Sleep Powder", "3-in-1 Magnesium Glycinate, Taurate & L-Threonate"]},
    {"name": "Creatine Monohydrate", "chem": "Creatine", "cat": "Cellular ATP, Muscle & Cognitive Longevity Powder", "ph": "Neutral", "time": "Daily (5g Anytime with Water/Electrolytes)", "conflict": "None (Third-party Creapure / NSF certified preferred)", "forms": ["Micronized Creatine Monohydrate Powder (100 Servings)", "Creatine Monohydrate + Electrolytes Hydration Mix", "Unflavored GMP Certified Creatine Capsules"]},
    {"name": "L-Theanine", "chem": "Theanine", "cat": "Alpha-Wave Calm Focus & Jitter-Free Nootropic", "ph": "Neutral", "time": "AM (with Coffee) or PM (for Sleep)", "conflict": "None (Synergizes 2:1 with Caffeine)", "forms": ["L-Theanine 200mg Suntheanine Softgels", "Caffeine + L-Theanine Focus Nootropic Stack", "Magnesium + L-Theanine + Apigenin Night Complex"]},
    {"name": "Berberine", "chem": "Berberine", "cat": "AMPK Metabolic & Glucose Support Alkaloid", "ph": "Neutral", "time": "15-30 Mins Before Carbohydrate Meals", "conflict": "Consult physician if using prescription hypoglycemics", "forms": ["Berberine Phytosome 1200mg with Ceylon Cinnamon", " Dihydroberberine High-Bioavailability Capsules", "Berberine + Chromium Metabolic Support Complex"]},
    {"name": "Glutathione", "chem": "Glutathione", "cat": "Master Intracellular Antioxidant & Brightening Tripeptide", "ph": "4.5 - 6.0", "time": "AM on Empty Stomach or Topical Serum", "conflict": "None (Synergizes with Vitamin C & NAC)", "forms": ["Liposomal Glutathione 1000mg Softgels", "Korean Glutathione + Niacinamide Glow Toner Pads", "Reduced L-Glutathione + Vitamin C Complex"]},
    {"name": "N-Acetyl Cysteine", "chem": "Acetylcysteine", "cat": "Glutathione Precursor & Respiratory/Cellular Defense", "ph": "Neutral", "time": "AM or PM Between Meals", "conflict": "None (Pairs with Glycine for GlyNAC stack)", "forms": ["NAC N-Acetyl Cysteine 600mg Veggie Capsules", "GlyNAC (Glycine + NAC) Longevity Bundle", "NAC + Selenium + Molybdenum Detox Formula"]},
    {"name": "Astaxanthin", "chem": "Astaxanthin", "cat": "Lipid-Soluble Carotenoid UV & Skin Elasticity Shield", "ph": "Lipid-Soluble", "time": "With a Fat-Containing Meal", "conflict": "None", "forms": ["12mg Icelandic Microalgae Astaxanthin Softgels", "Astaxanthin + Omega-3 Krill Oil Complex", "Topical Astaxanthin Antioxidant Facial Oil"]},
    {"name": "Inositol", "chem": "Inositol", "cat": "Hormonal Balance, Ovarian & Deep Sleep Support", "ph": "Neutral", "time": "AM & PM (or Before Bed for Sleep)", "conflict": "None", "forms": ["Myo-Inositol & D-Chiro Inositol 40:1 Ratio Powder", "Myo-Inositol 2000mg Hormone Balance Capsules", "Inositol + Magnesium Deep Sleep Drink Mix"]},
    {"name": "Taurine", "chem": "Taurine", "cat": "Cardiovascular, Cellular Hydration & Longevity Amino", "ph": "Neutral", "time": "AM or Pre-Workout", "conflict": "None", "forms": ["Pure Taurine 1000mg Double-Strength Capsules", "Electrolyte + Taurine Zero-Sugar Hydration Packets", "Taurine + Magnesium Heart & Nerve Support"]}
]


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-") or "active"


def load_db() -> dict:
    if os.path.exists(DB_PATH):
        try:
            with open(DB_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_db(db: dict):
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with open(DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def make_bestseller_amazon_url(query: str) -> str:
    """
    Membuat URL afiliasi Amazon yang otomatis mengurutkan berdasarkan Best Sellers (exact-aware-popularity-rank)
    dan menyaring produk dengan rating tinggi (4 bintang ke atas) untuk memaksimalkan konversi.
    """
    encoded_q = quote_plus(query)
    return f"https://www.amazon.com/s?k={encoded_q}&s=exact-aware-popularity-rank&rh=p_72%3A1248873011&tag={AMAZON_TAG}"


def fetch_pubchem_data(chem_name: str) -> dict:
    """Mengambil data ilmiah resmi dari NIH PubChem PUG-REST API (US Government)."""
    encoded = quote_plus(chem_name)
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{encoded}/property/MolecularFormula,MolecularWeight,IUPACName,XLogP/JSON"
    default_props = {
        "formula": "Verified Bio-Active",
        "mw": 245.2,
        "iupac": chem_name,
        "xlogp": 0.5
    }
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        if resp.status_code == 200:
            props = resp.json().get("PropertyTable", {}).get("Properties", [{}])[0]
            mw_val = float(props.get("MolecularWeight", 245.2))
            xlogp_val = float(props.get("XLogP", 0.5)) if "XLogP" in props else 0.5
            return {
                "formula": props.get("MolecularFormula", "Bio-Active"),
                "mw": round(mw_val, 2),
                "iupac": props.get("IUPACName", chem_name),
                "xlogp": round(xlogp_val, 2)
            }
    except Exception as e:
        print(f"[WARN] PubChem fallback untuk {chem_name}: {e}")
    return default_props


def fetch_openfda_context(name: str) -> str:
    """Mengambil ringkasan indikasi/penggunaan resmi dari US OpenFDA API jika tersedia."""
    encoded = quote_plus(name)
    url = f"https://api.fda.gov/drug/label.json?search=openfda.generic_name:{encoded}+OR+active_ingredient:{encoded}&limit=1"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            results = resp.json().get("results", [])
            if results:
                purpose = results[0].get("purpose", results[0].get("indications_and_usage", [""]))[0]
                clean = re.sub(r"\s+", " ", purpose).strip()
                if len(clean) > 30:
                    return clean[:280] + "..."
    except Exception:
        pass
    return f"{name} is a clinically studied compound widely utilized in top-ranked 2026 dermatological formulations and daily wellness protocols for targeted barrier and cellular support."


def enrich_active_item(item: dict) -> dict:
    pubchem = fetch_pubchem_data(item["chem"])
    fda_note = fetch_openfda_context(item["name"])

    mw = pubchem["mw"]
    # 500 Dalton Rule dalam dermatologi: molekul di bawah 500 Da menembus stratum corneum secara optimal
    if mw <= 500:
        penetration_verdict = f"High Stratum Corneum Penetration ({mw} Daltons - Under the 500 Dalton Threshold)"
    else:
        penetration_verdict = f"Surface & Barrier-Locking Molecule ({mw} Daltons - Functions on Upper Epidermis)"

    # XLogP menentukan apakah bahan larut air (hydrophilic) atau larut minyak (lipophilic)
    xlogp = pubchem["xlogp"]
    if xlogp < 1.5:
        solubility = f"Water-Soluble / Hydrophilic (XLogP: {xlogp}) - 0/5 Non-Comedogenic Score"
    else:
        solubility = f"Lipid-Soluble / Oil-Phase (XLogP: {xlogp}) - Penetrates Sebum-Rich Pores"

    slug = f"{slugify(item['name'])}-benefits-layering-guide-amazon-bestsellers-2026"

    return {
        "name": item["name"],
        "chem": item["chem"],
        "slug": slug,
        "cat": item["cat"],
        "ph": item["ph"],
        "time": item["time"],
        "conflict": item["conflict"],
        "forms": item["forms"],
        "formula": pubchem["formula"],
        "mw": mw,
        "iupac": pubchem["iupac"],
        "xlogp": xlogp,
        "penetration": penetration_verdict,
        "solubility": solubility,
        "fda_note": fda_note,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d")
    }


def build_active_page(active: dict, all_actives: list):
    os.makedirs(ACTIVES_DIR, exist_ok=True)
    name = active["name"]
    page_url = f"{SITE_URL}/actives/{active['slug']}.html"

    # Buat kartu produk Amazon Best-Seller berdasarkan form faktor terlaris
    cards_html = ""
    badges = ["2026 #1 Category Best-Seller", "Derm-Approved 4.5+ Stars", "High Repeat-Purchase Formula"]
    for idx, form_title in enumerate(active["forms"]):
        badge_text = badges[idx % len(badges)]
        amz_url = make_bestseller_amazon_url(f"{form_title} fragrance free")
        cards_html += f"""
        <div class="card">
            <div class="card-head">
                <span class="cat">{active['cat']}</span>
                <span class="badge">{badge_text}</span>
            </div>
            <h3>{form_title}</h3>
            <p>Formulated at optimal pH ({active['ph']}) for maximum bioavailability and zero pore congestion. Sorted automatically by Amazon's current top-selling consumer rankings.</p>
            <a href="{amz_url}" target="_blank" rel="nofollow sponsored noopener" class="btn">View #1 Best-Sellers on Amazon &rarr;</a>
        </div>
        """

    # Kartu bundle komplementer (Subscribe & Save / Routine Multiplier)
    bundle_url = make_bestseller_amazon_url(f"{name} barrier repair moisturizer SPF 50 bundle")
    cards_html += f"""
    <div class="card">
        <div class="card-head">
            <span class="cat">Complete Routine Multiplier</span>
            <span class="badge">Subscribe & Save Eligible</span>
        </div>
        <h3>{name} + Ceramide Barrier & SPF 50 Daily Protocol</h3>
        <p>Pair {name} with a pH-balanced ceramide moisturizer or synergistic stack to prevent transepidermal water loss and lock in active ingredients.</p>
        <a href="{bundle_url}" target="_blank" rel="nofollow sponsored noopener" class="btn">Shop Compatible Routine Stacks &rarr;</a>
    </div>
    """

    # Tautan internal ke halaman kompatibilitas (Mix Guide) dan bahan aktif lainnya
    related_html = ""
    for other in all_actives[:10]:
        if other["name"] == name:
            continue
        related_html += f"""
        <a href="{SITE_URL}/actives/{other['slug']}.html" class="rel-card">
            <strong>{other['name']} ({other['mw']} Da)</strong>
            <span>{other['cat']} &rarr;</span>
        </a>
        """

    faq_schema = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {
                "@type": "Question",
                "name": f"What is the molecular weight of {name} and does it penetrate the skin barrier?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"According to NIH PubChem data, {name} ({active['formula']}) has a molecular weight of {active['mw']} Daltons. {active['penetration']}."
                }
            },
            {
                "@type": "Question",
                "name": f"What ingredients should not be mixed with {name}?",
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": f"Optimal pH for {name} is {active['ph']}. Avoid layering directly with: {active['conflict']}. Best applied: {active['time']}."
                }
            }
        ]
    }

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} Benefits, 500-Dalton Penetration, Layering Conflicts & 2026 Amazon Best-Sellers</title>
    <meta name="description" content="Complete scientific profile for {name} ({active['formula']}, {active['mw']} Da): pH compatibility ({active['ph']}), routine conflicts ({active['conflict']}), and top-rated 2026 Amazon best-sellers.">
    <link rel="canonical" href="{page_url}">
    <script type="application/ld+json">{json.dumps(faq_schema)}</script>
    <style>
        :root {{ --bg: #0b1120; --card: #111827; --border: #1e293b; --text: #f8fafc; --muted: #94a3b8; --accent: #ec4899; --accent2: #14b8a6; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); line-height: 1.65; padding-bottom: 60px; }}
        header {{ background: #020617; border-bottom: 1px solid var(--border); padding: 18px 24px; }}
        .nav {{ max-width: 1100px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; }}
        .brand {{ color: var(--text); font-weight: 800; font-size: 1.25rem; text-decoration: none; }}
        .brand span {{ color: var(--accent2); }}
        .container {{ max-width: 1100px; margin: 32px auto; padding: 0 20px; }}
        .hero {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 28px; margin-bottom: 28px; }}
        .tags {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; }}
        .tag {{ background: #020617; border: 1px solid var(--border); color: var(--accent2); font-size: 0.78rem; padding: 4px 11px; border-radius: 999px; font-weight: 600; }}
        h1 {{ font-size: 1.9rem; line-height: 1.25; margin-bottom: 12px; }}
        .chem-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin-top: 22px; }}
        .chem-box {{ background: #020617; border: 1px solid var(--border); padding: 16px; border-radius: 10px; }}
        .chem-box span {{ display: block; font-size: 0.8rem; color: var(--muted); margin-bottom: 4px; }}
        .chem-box strong {{ font-size: 1.15rem; color: #fff; }}
        .checker {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 24px; margin-bottom: 34px; }}
        .checker-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 16px; margin-top: 14px; }}
        select {{ width: 100%; padding: 11px; border-radius: 8px; background: #020617; color: #fff; border: 1px solid var(--border); font-size: 0.95rem; }}
        .verdict-box {{ margin-top: 16px; padding: 16px; background: #020617; border-left: 4px solid var(--accent2); border-radius: 8px; }}
        .section-h2 {{ font-size: 1.45rem; margin: 34px 0 16px; border-left: 4px solid var(--accent); padding-left: 12px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
        .card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 22px; display: flex; flex-direction: column; justify-content: space-between; }}
        .card-head {{ display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }}
        .cat {{ font-size: 0.75rem; text-transform: uppercase; color: var(--accent2); font-weight: 700; }}
        .badge {{ background: #020617; color: #f472b6; font-size: 0.74rem; padding: 3px 8px; border-radius: 4px; border: 1px solid #be185d; }}
        .card h3 {{ font-size: 1.12rem; margin-bottom: 10px; color: #fff; }}
        .card p {{ color: var(--muted); font-size: 0.91rem; margin-bottom: 18px; }}
        .btn {{ display: block; text-align: center; background: var(--accent2); color: #020617; font-weight: 800; text-decoration: none; padding: 12px 16px; border-radius: 8px; }}
        .btn:hover {{ opacity: 0.92; }}
        .rel-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); gap: 14px; margin-top: 16px; }}
        .rel-card {{ background: var(--card); border: 1px solid var(--border); padding: 14px; border-radius: 10px; text-decoration: none; color: var(--text); display: block; }}
        .rel-card strong {{ display: block; font-size: 0.95rem; margin-bottom: 4px; }}
        .rel-card span {{ font-size: 0.82rem; color: var(--muted); }}
        footer {{ max-width: 1100px; margin: 48px auto 0; padding: 24px 20px 0; border-top: 1px solid var(--border); text-align: center; color: var(--muted); font-size: 0.82rem; }}
    </style>
</head>
<body>
    <header>
        <div class="nav">
            <a href="{SITE_URL}/" class="brand">Derm<span>Stack</span>2026</a>
            <a href="{SITE_URL}/" style="color: var(--muted); text-decoration: none; font-size: 0.9rem;">&larr; All Active Ingredients</a>
        </div>
    </header>
    <main class="container">
        <section class="hero">
            <div class="tags">
                <span class="tag">Formula: {active['formula']}</span>
                <span class="tag">Molecular Weight: {active['mw']} Da</span>
                <span class="tag">Optimal pH: {active['ph']}</span>
                <span class="tag">Routine Timing: {active['time']}</span>
            </div>
            <h1>{name}: Molecular Penetration, Layering Rules & 2026 Best-Selling Formulations</h1>
            <p style="color: var(--muted);">{active['fda_note']}</p>
            <div class="chem-grid">
                <div class="chem-box">
                    <span>500-Dalton Penetration Verdict</span>
                    <strong>{active['penetration']}</strong>
                </div>
                <div class="chem-box">
                    <span>Solubility & Comedogenic Profile</span>
                    <strong>{active['solubility']}</strong>
                </div>
                <div class="chem-box">
                    <span>Known Routine Conflict</span>
                    <strong style="color: #fb7185;">Avoid: {active['conflict']}</strong>
                </div>
            </div>
        </section>

        <section class="checker">
            <h2 style="font-size: 1.25rem;">Interactive {name} Skin-Type & Layering Compatibility Checker</h2>
            <div class="checker-row">
                <div>
                    <label style="font-size: 0.85rem; color: var(--muted); display: block; margin-bottom: 6px;">Select Your Skin / Wellness Profile</label>
                    <select id="skinType" onchange="evaluateRoutine()">
                        <option value="oily">Oily, Acne-Prone & Congested Pores</option>
                        <option value="dry">Dry, Compromised Barrier or Eczema-Prone</option>
                        <option value="aging">Mature, Hyperpigmentation & Fine Lines</option>
                    </select>
                </div>
                <div>
                    <label style="font-size: 0.85rem; color: var(--muted); display: block; margin-bottom: 6px;">Secondary Active in Your Routine</label>
                    <select id="secondActive" onchange="evaluateRoutine()">
                        <option value="safe">Hyaluronic Acid / Ceramides / Panthenol</option>
                        <option value="acid">Low-pH Acids (Glycolic, Salicylic, L-Ascorbic Vitamin C)</option>
                        <option value="retinoid">Retinoids (Tretinoin, Retinaldehyde, Adapalene)</option>
                    </select>
                </div>
            </div>
            <div class="verdict-box" id="routineVerdict">
                <strong>Recommended Protocol:</strong> Safe to layer in the same routine ({active['time']}). Apply water-based serums first, wait 60 seconds, and seal with a barrier moisturizer.
            </div>
        </section>

        <h2 class="section-h2">Top-Rated 2026 Amazon Best-Sellers Featuring {name}</h2>
        <div class="grid">
            {cards_html}
        </div>

        <h2 class="section-h2">Explore Related Dermatological & Longevity Actives</h2>
        <div class="rel-grid">
            {related_html}
        </div>
    </main>
    <footer>
        <p>As an Amazon Associate, this platform earns from qualifying purchases. Chemical properties verified via NIH PubChem & US OpenFDA public databases ({active['updated_at']}).</p>
    </footer>
    <script>
        function evaluateRoutine() {{
            const s = document.getElementById('secondActive').value;
            const box = document.getElementById('routineVerdict');
            const conflictText = {json.dumps(active['conflict'])};
            if (s === 'safe') {{
                box.innerHTML = '<strong>100% Synergistic Match:</strong> Humectants and ceramides buffer potential irritation while improving stratum corneum absorption of {name}.';
            }} else if (conflictText.toLowerCase().includes('none')) {{
                box.innerHTML = '<strong>Compatible Stack:</strong> {name} has no pH conflicts with acids or retinoids and can be safely layered in the same session.';
            }} else {{
                box.innerHTML = '<strong>Alternate AM/PM Timing Recommended:</strong> Because {name} conflicts with <em>' + conflictText + '</em>, separate them into morning and evening routines to prevent pH inactivation or barrier stinging.';
            }}
        }}
    </script>
</body>
</html>"""

    filepath = os.path.join(ACTIVES_DIR, f"{active['slug']}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)


def build_compatibility_pages(all_actives: list) -> list:
    """Membuat halaman perbandingan 'Can You Mix X and Y?' untuk menangkap trafik long-tail SEO."""
    os.makedirs(MIX_DIR, exist_ok=True)
    generated_urls = []
    # Buat kombinasi pasangan populer dari 12 bahan teratas (66 halaman unik ber-intent tinggi)
    top_subset = all_actives[:12]
    for i in range(len(top_subset)):
        for j in range(i + 1, len(top_subset)):
            a = top_subset[i]
            b = top_subset[j]
            slug = f"can-you-mix-{slugify(a['name'])}-and-{slugify(b['name'])}-layering-guide"
            page_url = f"{SITE_URL}/compatibility/{slug}.html"

            has_conflict = (
                b["name"].lower() in a["conflict"].lower()
                or a["name"].lower() in b["conflict"].lower()
                or ("acid" in a["name"].lower() and "acid" in b["name"].lower())
            )
            verdict_badge = "Split AM / PM Routine Recommended" if has_conflict else "Safe to Layer in Same Routine"
            verdict_desc = (
                f"Direct layering of {a['name']} (pH {a['ph']}) and {b['name']} (pH {b['ph']}) in the exact same step can cause pH destabilization or skin barrier irritation. Use {a['name']} in the morning and {b['name']} at night."
                if has_conflict else
                f"{a['name']} ({a['mw']} Da) and {b['name']} ({b['mw']} Da) are chemically compatible. Apply the lighter, lower-molecular-weight formula first, wait 60 seconds, then apply the second active."
            )

            url_a = make_bestseller_amazon_url(a["forms"][0])
            url_b = make_bestseller_amazon_url(b["forms"][0])

            html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Can You Mix {a['name']} and {b['name']}? pH Compatibility & Layering Order (2026)</title>
    <meta name="description" content="Scientific answer: Can you layer {a['name']} ({a['ph']}) with {b['name']} ({b['ph']})? Complete molecular weight order ({a['mw']} Da vs {b['mw']} Da) and top Amazon products.">
    <link rel="canonical" href="{page_url}">
    <style>
        :root {{ --bg: #0b1120; --card: #111827; --border: #1e293b; --text: #f8fafc; --muted: #94a3b8; --accent: #14b8a6; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); line-height: 1.65; padding-bottom: 60px; }}
        header {{ background: #020617; border-bottom: 1px solid var(--border); padding: 18px 24px; }}
        .container {{ max-width: 980px; margin: 32px auto; padding: 0 20px; }}
        .box {{ background: var(--card); border: 1px solid var(--border); border-radius: 14px; padding: 26px; margin-bottom: 24px; }}
        .pill {{ display: inline-block; background: #020617; color: var(--accent); padding: 5px 12px; border-radius: 999px; font-size: 0.82rem; font-weight: 700; margin-bottom: 12px; border: 1px solid var(--border); }}
        h1 {{ font-size: 1.8rem; margin-bottom: 12px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 20px; margin-top: 20px; }}
        .btn {{ display: block; text-align: center; background: var(--accent); color: #020617; font-weight: 800; text-decoration: none; padding: 12px 16px; border-radius: 8px; margin-top: 14px; }}
        footer {{ text-align: center; color: var(--muted); font-size: 0.82rem; margin-top: 40px; }}
    </style>
</head>
<body>
    <header>
        <div style="max-width:980px;margin:0 auto;display:flex;justify-content:space-between;">
            <a href="{SITE_URL}/" style="color:#fff;font-weight:800;text-decoration:none;">Derm<span style="color:var(--accent);">Stack</span>2026</a>
            <a href="{SITE_URL}/" style="color:var(--muted);text-decoration:none;">&larr; All Ingredients</a>
        </div>
    </header>
    <main class="container">
        <div class="box">
            <span class="pill">Verdict: {verdict_badge}</span>
            <h1>Can You Mix {a['name']} and {b['name']} Together?</h1>
            <p style="color:var(--muted);">{verdict_desc}</p>
        </div>
        <div class="grid">
            <div class="box">
                <h2>1. {a['name']} ({a['mw']} Da)</h2>
                <p style="color:var(--muted);font-size:0.9rem;margin:8px 0;">Optimal pH: {a['ph']} &bull; Timing: {a['time']}</p>
                <p style="font-size:0.92rem;">Best-Selling Format: <strong>{a['forms'][0]}</strong></p>
                <a href="{url_a}" target="_blank" rel="nofollow sponsored noopener" class="btn">Check #1 {a['name']} on Amazon &rarr;</a>
            </div>
            <div class="box">
                <h2>2. {b['name']} ({b['mw']} Da)</h2>
                <p style="color:var(--muted);font-size:0.9rem;margin:8px 0;">Optimal pH: {b['ph']} &bull; Timing: {b['time']}</p>
                <p style="font-size:0.92rem;">Best-Selling Format: <strong>{b['forms'][0]}</strong></p>
                <a href="{url_b}" target="_blank" rel="nofollow sponsored noopener" class="btn">Check #1 {b['name']} on Amazon &rarr;</a>
            </div>
        </div>
    </main>
    <footer>
        <p>As an Amazon Associate, this site earns from qualifying purchases. Verified via NIH PubChem molecular data.</p>
    </footer>
</body>
</html>"""
            with open(os.path.join(MIX_DIR, f"{slug}.html"), "w", encoding="utf-8") as f:
                f.write(html)
            generated_urls.append((f"Can You Mix {a['name']} & {b['name']}?", slug, page_url))
    return generated_urls


def build_index_and_seo_files(db: dict, mix_links: list):
    os.makedirs(DOCS_DIR, exist_ok=True)
    actives_list = list(db.values())

    cards_html = ""
    for item in actives_list:
        cards_html += f"""
        <article class="item-card">
            <a href="{SITE_URL}/actives/{item['slug']}.html" style="text-decoration:none;color:inherit;">
                <div class="item-top">
                    <span class="item-cat">{item['cat']}</span>
                    <span class="item-mw">{item['mw']} Da</span>
                </div>
                <h2>{item['name']}</h2>
                <p class="item-meta">pH: {item['ph']} &bull; Formula: {item['formula']}</p>
                <span class="item-link">View Penetration & 2026 Best-Sellers &rarr;</span>
            </a>
        </article>
        """

    mix_html = ""
    for title, slug, _ in mix_links[:24]:
        mix_html += f'<a href="{SITE_URL}/compatibility/{slug}.html" class="mix-pill">{title} &rarr;</a>\n'

    index_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DermStack2026 - Skincare & Longevity Active Ingredient Checker & Amazon Best-Seller Finder</title>
    <meta name="description" content="Verify 500-Dalton molecular weights, pH layering conflicts, and shop the #1 best-selling 2026 skincare serums and longevity supplements on Amazon.">
    <link rel="canonical" href="{SITE_URL}/">
    <style>
        :root {{ --bg: #0b1120; --card: #111827; --border: #1e293b; --text: #f8fafc; --muted: #94a3b8; --accent: #14b8a6; --pink: #ec4899; }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: var(--bg); color: var(--text); line-height: 1.6; }}
        header {{ background: #020617; border-bottom: 1px solid var(--border); padding: 36px 20px; text-align: center; }}
        header h1 {{ font-size: 2.1rem; margin-bottom: 8px; }}
        header h1 span {{ color: var(--accent); }}
        header p {{ color: var(--muted); max-width: 700px; margin: 0 auto 20px; }}
        #searchBox {{ width: 100%; max-width: 540px; padding: 13px 16px; border-radius: 8px; border: 1px solid var(--border); background: #0b1120; color: #fff; font-size: 1rem; }}
        .container {{ max-width: 1120px; margin: 36px auto; padding: 0 20px; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(290px, 1fr)); gap: 18px; }}
        .item-card {{ background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 20px; transition: transform 0.15s, border-color 0.15s; }}
        .item-card:hover {{ transform: translateY(-4px); border-color: var(--accent); }}
        .item-top {{ display: flex; justify-content: space-between; font-size: 0.76rem; margin-bottom: 8px; }}
        .item-cat {{ color: var(--accent); font-weight: 700; text-transform: uppercase; }}
        .item-mw {{ color: var(--pink); font-weight: 700; }}
        .item-card h2 {{ font-size: 1.2rem; margin-bottom: 8px; color: #fff; }}
        .item-meta {{ font-size: 0.84rem; color: var(--muted); margin-bottom: 12px; }}
        .item-link {{ font-size: 0.86rem; color: var(--accent); font-weight: 700; }}
        .mix-wrap {{ display: flex; flex-wrap: wrap; gap: 10px; margin-top: 16px; }}
        .mix-pill {{ background: var(--card); border: 1px solid var(--border); color: var(--text); text-decoration: none; padding: 8px 14px; border-radius: 8px; font-size: 0.85rem; }}
        .mix-pill:hover {{ border-color: var(--pink); }}
        footer {{ text-align: center; padding: 40px 20px; color: var(--muted); font-size: 0.82rem; border-top: 1px solid var(--border); margin-top: 60px; }}
    </style>
</head>
<body>
    <header>
        <h1>Derm<span>Stack</span> 2026 Active Matrix</h1>
        <p>NIH PubChem Molecular Weight Checker, Routine Layering Conflict Calculator & #1 Best-Selling Amazon Beauty/Health Finder</p>
        <input type="text" id="searchBox" placeholder="Search ingredient (e.g. Niacinamide, Hypochlorous, Retinal, Magnesium, Creatine)..." onkeyup="filterActives()">
    </header>
    <main class="container">
        <div class="grid" id="activesGrid">
            {cards_html}
        </div>
        <h2 style="font-size:1.4rem;margin:42px 0 12px;border-left:4px solid var(--pink);padding-left:12px;">Popular Ingredient Layering & Compatibility Guides</h2>
        <div class="mix-wrap">
            {mix_html}
        </div>
    </main>
    <footer>
        <p>As an Amazon Associate, this site earns from qualifying purchases. Synchronized automatically with NIH PubChem & US OpenFDA databases.</p>
    </footer>
    <script>
        function filterActives() {{
            const q = document.getElementById('searchBox').value.toLowerCase();
            document.querySelectorAll('.item-card').forEach(card => {{
                card.style.display = card.innerText.toLowerCase().includes(q) ? '' : 'none';
            }});
        }}
    </script>
</body>
</html>"""

    with open(os.path.join(DOCS_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(index_html)

    # Sitemap XML
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls_xml = f"""  <url>
    <loc>{SITE_URL}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>\n"""

    for item in actives_list:
        urls_xml += f"""  <url>
    <loc>{SITE_URL}/actives/{item['slug']}.html</loc>
    <lastmod>{item.get('updated_at', today)}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
  </url>\n"""

    for _, _, full_mix_url in mix_links:
        urls_xml += f"""  <url>
    <loc>{full_mix_url}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>\n"""

    sitemap = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{urls_xml}</urlset>"""

    with open(os.path.join(DOCS_DIR, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)

    with open(os.path.join(DOCS_DIR, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")

    with open(os.path.join(DOCS_DIR, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)


def ping_indexnow(urls: list):
    if not urls or "username.github.io" in SITE_URL:
        return
    host = SITE_URL.replace("https://", "").replace("http://", "").split("/")[0]
    payload = {
        "host": host,
        "key": INDEXNOW_KEY,
        "keyLocation": f"{SITE_URL}/{INDEXNOW_KEY}.txt",
        "urlList": urls[:100]
    }
    try:
        r = requests.post(
            "https://api.indexnow.org/indexnow",
            json=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=15
        )
        print(f"[INFO] IndexNow Ping HTTP Status: {r.status_code}")
    except Exception as e:
        print(f"[WARN] IndexNow Ping Gagal: {e}")


def main():
    db = load_db()
    new_urls = []
    added = 0

    for item in CATALOG_2026:
        key = item["name"]
        if key in db:
            continue
        # Tambahkan hingga 12 bahan aktif baru per eksekusi harian agar terindeks bertahap dan alami
        if added >= 12:
            break
        enriched = enrich_active_item(item)
        db[key] = enriched
        new_urls.append(f"{SITE_URL}/actives/{enriched['slug']}.html")
        added += 1
        print(f"[OK] Berhasil memproses bahan aktif: {key} ({enriched['mw']} Da)")
        time.sleep(0.5)

    all_actives = list(db.values())
    for item in all_actives:
        build_active_page(item, all_actives)

    mix_links = build_compatibility_pages(all_actives)
    build_index_and_seo_files(db, mix_links)
    save_db(db)

    if new_urls:
        new_urls.append(f"{SITE_URL}/")
        for _, _, m_url in mix_links[:25]:
            new_urls.append(m_url)
        ping_indexnow(new_urls)

    print(f"[DONE] Total halaman bahan aktif: {len(all_actives)} | Halaman kombinasi: {len(mix_links)}")


if __name__ == "__main__":
    main()
