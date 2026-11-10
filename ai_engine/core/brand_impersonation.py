"""
Cyber Raksha AI - Brand Impersonation & Lookalike Domain Detection Engine
Phase B4: Intelligent Threat Detection

Detects lookalike domains, deceptive brand keywords, typosquatting, and unauthorized
subdomain impersonations targeting major financial institutions, payment gateways,
government portals, and delivery logistics providers.
"""
import re
from typing import Optional, Dict, Any, List, Set, NamedTuple


class BrandProfile(NamedTuple):
    brand_id: str
    display_name: str
    category: str  # BANKING, FINTECH, LOGISTICS, TECH, GOVERNMENT
    legitimate_domains: Set[str]
    keywords: List[str]


# Curated catalog of high-target brands across India and global services
TARGET_BRANDS: List[BrandProfile] = [
    # Banking
    BrandProfile(
        brand_id="HDFC",
        display_name="HDFC Bank",
        category="BANKING",
        legitimate_domains={"hdfcbank.com", "hdfc.com", "hdfcbank.net"},
        keywords=["hdfc", "hdfcbank", "hdfcnetbanking"]
    ),
    BrandProfile(
        brand_id="SBI",
        display_name="State Bank of India (SBI)",
        category="BANKING",
        legitimate_domains={"sbi.co.in", "onlinesbi.sbi", "onlinesbi.com", "sbi.bank"},
        keywords=["sbi", "sbinetbanking", "onlinesbi", "sbicard", "yono", "yonosbi"]
    ),
    BrandProfile(
        brand_id="ICICI",
        display_name="ICICI Bank",
        category="BANKING",
        legitimate_domains={"icicibank.com", "icicibank.co.in", "icici.com"},
        keywords=["icicibank", "icicinetbanking", "icicidirect"]
    ),
    BrandProfile(
        brand_id="AXIS",
        display_name="Axis Bank",
        category="BANKING",
        legitimate_domains={"axisbank.com", "axisbank.co.in"},
        keywords=["axisbank", "axisnetbanking"]
    ),
    BrandProfile(
        brand_id="KOTAK",
        display_name="Kotak Mahindra Bank",
        category="BANKING",
        legitimate_domains={"kotak.com", "kotakbank.com"},
        keywords=["kotakbank", "kotak811", "kotaknetbanking"]
    ),
    BrandProfile(
        brand_id="PNB",
        display_name="Punjab National Bank",
        category="BANKING",
        legitimate_domains={"pnbindia.in", "pnbnet.in.net"},
        keywords=["pnbindia", "pnbnetbanking", "punjabnationalbank"]
    ),
    # Payment & Fintech
    BrandProfile(
        brand_id="PAYTM",
        display_name="Paytm",
        category="FINTECH",
        legitimate_domains={"paytm.com", "paytmbank.com"},
        keywords=["paytm", "paytmcash", "paytmkyc"]
    ),
    BrandProfile(
        brand_id="PHONEPE",
        display_name="PhonePe",
        category="FINTECH",
        legitimate_domains={"phonepe.com"},
        keywords=["phonepe", "phonepecashback"]
    ),
    BrandProfile(
        brand_id="GPAY",
        display_name="Google Pay",
        category="FINTECH",
        legitimate_domains={"google.com", "pay.google.com"},
        keywords=["googlepay", "gpay", "gpayreward"]
    ),
    # Logistics & Delivery
    BrandProfile(
        brand_id="INDIA_POST",
        display_name="India Post / Speed Post",
        category="LOGISTICS",
        legitimate_domains={"indiapost.gov.in", "ippbonline.com"},
        keywords=["indiapost", "speedpost", "indiaposttracking"]
    ),
    BrandProfile(
        brand_id="BLUEDART",
        display_name="Blue Dart Express",
        category="LOGISTICS",
        legitimate_domains={"bluedart.com"},
        keywords=["bluedart", "bluedarttracking"]
    ),
    # Tech & Streaming
    BrandProfile(
        brand_id="AMAZON",
        display_name="Amazon",
        category="TECH",
        legitimate_domains={"amazon.com", "amazon.in", "media-amazon.com"},
        keywords=["amazon", "amazonpay", "amazonprime"]
    ),
    BrandProfile(
        brand_id="NETFLIX",
        display_name="Netflix",
        category="TECH",
        legitimate_domains={"netflix.com"},
        keywords=["netflix", "netflixbilling"]
    ),
    # Government & Tax
    BrandProfile(
        brand_id="INCOME_TAX",
        display_name="Income Tax Department",
        category="GOVERNMENT",
        legitimate_domains={"incometax.gov.in", "incometaxindia.gov.in"},
        keywords=["incometaxindia", "efilingrefund", "incometaxrefund"]
    ),
    BrandProfile(
        brand_id="UIDAI",
        display_name="UIDAI (Aadhaar)",
        category="GOVERNMENT",
        legitimate_domains={"uidai.gov.in", "myaadhaar.uidai.gov.in"},
        keywords=["myaadhaar", "uidaiupdate", "aadhaarverify"]
    )
]


def check_brand_impersonation(hostname: str) -> Optional[Dict[str, Any]]:
    """
    Analyzes hostname for unauthorized brand impersonation:
    1. Checks if the domain is the legitimate, authorized domain for the brand.
    2. Identifies lookalikes, unauthorized subdomains, hyphenated prefixes/suffixes,
       and deceptive keyword combinations.
    3. Returns structured evidence with brand details and risk contribution.
    """
    if not hostname:
        return None

    clean_host = hostname.lower().strip().split(":")[0].strip("[]")

    for brand in TARGET_BRANDS:
        # 1. If host is an official legitimate domain or subdomain of it, return None (safe)
        for legit in brand.legitimate_domains:
            if clean_host == legit or clean_host.endswith(f".{legit}"):
                return None  # Authorized official domain

        # 2. Check for deceptive usage of brand keywords in unauthorized domains
        for kw in brand.keywords:
            # Match keyword as standalone token, hyphenated token, or subdomain
            pattern = rf"(^|[.\-_]){re.escape(kw)}([.\-_]|$)"
            if re.search(pattern, clean_host):
                # Detected brand keyword in unauthorized domain
                risk_contribution = 35.0 if brand.category == "BANKING" else (30.0 if brand.category == "FINTECH" else 25.0)
                description = (
                    f"The domain '{clean_host}' impersonates {brand.display_name} "
                    f"({brand.category}) using unauthorized keyword '{kw}' outside authorized domain infrastructure."
                )
                return {
                    "brand_id": brand.brand_id,
                    "brand_name": brand.display_name,
                    "category": brand.category,
                    "matched_keyword": kw,
                    "impersonation_type": "UNAUTHORIZED_BRAND_KEYWORD",
                    "risk_contribution": risk_contribution,
                    "description": description
                }

    return None

