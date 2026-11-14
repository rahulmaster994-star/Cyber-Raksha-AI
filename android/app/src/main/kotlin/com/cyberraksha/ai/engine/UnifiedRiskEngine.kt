package com.cyberraksha.ai.engine

import java.util.regex.Pattern

data class RiskAssessment(
    val category: String,
    val severity: String, // LOW, MEDIUM, HIGH, CRITICAL
    val riskScore: Float, // 0.0 to 100.0
    val reasons: List<String>,
    val recommendedAction: String,
    val extractedUrls: List<String>
)

object UnifiedRiskEngine {

    // 10 Comprehensive Fraud Categories with High-Precision Signatures
    private val PATTERNS = mapOf(
        "GOV_IMPERSONATION" to listOf(
            Regex("""\bdigital\s+arrest\b""", RegexOption.IGNORE_CASE),
            Regex("""\bcbi\s+(?:notice|order|department|officer|summons|investigation)\b""", RegexOption.IGNORE_CASE),
            Regex("""\bpolice\s+(?:warrant|arrest|summons|fir|custody|investigation)\b""", RegexOption.IGNORE_CASE),
            Regex("""\bnarcotics\s+(?:control|bureau|drugs|parcel|seizure)\b""", RegexOption.IGNORE_CASE),
            Regex("""\bcustoms\s+(?:seizure|confiscation|held|parcel|illegal)\b""", RegexOption.IGNORE_CASE),
            Regex("""\bcyber\s+crime\s+(?:branch|police|department|complaint|cell)\b""", RegexOption.IGNORE_CASE),
            Regex("""\bcourt\s+summons\b""", RegexOption.IGNORE_CASE),
            Regex("""\bed\s+(?:raid|notice|inquiry|investigation)\b""", RegexOption.IGNORE_CASE),
            Regex("""\b(?:arrest\s+warrant|money\s+laundering|skype\s+hearing|digital\s+hearing)\b""", RegexOption.IGNORE_CASE)
        ),
        "OTP_THEFT" to listOf(
            Regex("""\bshare\s+(?:your\s+)?(?:otp|one\s+time\s+password|pin)\b""", RegexOption.IGNORE_CASE),
            Regex("""\b(?:asking|demanding|requesting)\s+(?:for\s+)?(?:the\s+|your\s+)?otp\b""", RegexOption.IGNORE_CASE),
            Regex("""\botp\s+(?:for|to)\s+(?:verification|receive|refund|claim|activation|verify)\b""", RegexOption.IGNORE_CASE),
            Regex("""\btell\s+(?:me\s+)?(?:the\s+)?(?:otp|6\s*digit\s*code|pin)\b""", RegexOption.IGNORE_CASE),
            Regex("""\bsend\s+(?:back\s+)?otp\b""", RegexOption.IGNORE_CASE),
            Regex("""\bforward\s+(?:this\s+)?(?:otp|sms)\b""", RegexOption.IGNORE_CASE),
            Regex("""\benter\s+otp\s+to\s+receive\b""", RegexOption.IGNORE_CASE)
        ),
        "UPI_FRAUD" to listOf(
            Regex("""\benter\s+(?:your\s+)?upi\s*pin\s+(?:to\s+)?(?:receive|get|claim)\b""", RegexOption.IGNORE_CASE),
            Regex("""\b(?:enter|share)\s+(?:your\s+)?upi\s*(?:pin|id)\b""", RegexOption.IGNORE_CASE),
            Regex("""\bcollect\s+request\b""", RegexOption.IGNORE_CASE),
            Regex("""\b(?:paytm|phonepe|gpay|bhim)\s+(?:cashback|reward|winner|request)\b""", RegexOption.IGNORE_CASE),
            Regex("""\bscan\s+(?:this\s+)?qr\s*(?:code)?\b""", RegexOption.IGNORE_CASE),
            Regex("""\bapprove\s+(?:the\s+)?request\s+to\s+(?:get|receive)\b""", RegexOption.IGNORE_CASE),
            Regex("""\brefund\s+(?:of\s+rs\.?|credited|approved)\b""", RegexOption.IGNORE_CASE)
        ),
        "BANKING_FRAUD" to listOf(
            // Account blocking/suspension threats with flexible tense ("will be blocked", "has been blocked", "to avoid permanent suspension")
            Regex("""\b(?:bank\s+)?account\s+(?:will\s+be|is|has\s+been|was|to\s+be|going\s+to\s+be)?\s*(?:temporarily\s+|permanently\s+)?(?:blocked|suspended|deactivated|frozen|closed)\b""", RegexOption.IGNORE_CASE),
            Regex("""\bkyc\s+(?:verification\s+|details\s+)?(?:is|has|status)?\s*(?:been\s+)?(?:pending|expired|suspended|required|failed|incomplete)\b""", RegexOption.IGNORE_CASE),
            Regex("""\b(?:provide|enter|submit|share|update)\s+(?:your\s+)?(?:banking\s+|login\s+|account\s+)?credentials\b""", RegexOption.IGNORE_CASE),
            Regex("""\b(?:avoid|prevent)\s+(?:permanent\s+|account\s+)?(?:suspension|deactivation|blocking|closure)\b""", RegexOption.IGNORE_CASE),
            Regex("""\b(?:immediately\s+verify|verify\s+(?:your\s+)?(?:bank\s+)?account)\b""", RegexOption.IGNORE_CASE),
            Regex("""\b(?:update|verify|link|validate)\s+(?:your\s+)?(?:pan|aadhaar|kyc)\b""", RegexOption.IGNORE_CASE),
            Regex("""\bnet\s*banking\s+(?:access\s+)?(?:suspended|blocked|expired)\b""", RegexOption.IGNORE_CASE),
            Regex("""\bunauthorized\s+(?:transaction|login|debit|access)\b""", RegexOption.IGNORE_CASE),
            Regex("""\b(?:sbi|hdfc|icici|axis|pnb|bob|kotak|canara|union\s*bank|bank\s*of\s*baroda)\s*(?:bank)?\s*(?:account|yono|netbanking)?\s*(?:is|has\s+been|will\s+be)?\s*(?:blocked|alert|kyc|suspended)\b""", RegexOption.IGNORE_CASE)
        ),
        "DELIVERY_SCAM" to listOf(
            Regex("""\b(?:parcel|package|courier|shipment)\s+(?:is\s+)?(?:on\s+hold|held|undelivered|delayed)\b""", RegexOption.IGNORE_CASE),
            Regex("""\bupdate\s+(?:delivery\s+)?address\s+(?:within|now|immediately)\b""", RegexOption.IGNORE_CASE),
            Regex("""\bpay\s+(?:pending\s+)?delivery\s+(?:fee|charges|cost)\b""", RegexOption.IGNORE_CASE),
            Regex("""\b(?:indiapost|delhivery|bluedart|speedpost)\s+(?:delivery|parcel|tracking)\b""", RegexOption.IGNORE_CASE)
        ),
        "LOTTERY_SCAM" to listOf(
            Regex("""\b(?:won|winner|congratulations)\s+(?:lottery|prize|lucky\s*draw|reward)\b""", RegexOption.IGNORE_CASE),
            Regex("""\bkbc\s+(?:lottery|winner|jackpot)\b""", RegexOption.IGNORE_CASE),
            Regex("""\bclaim\s+(?:your\s+)?(?:prize|car|cash|reward)\b""", RegexOption.IGNORE_CASE)
        ),
        "LOAN_SCAM" to listOf(
            Regex("""\binstant\s+(?:personal\s+)?loan\s+approved\b""", RegexOption.IGNORE_CASE),
            Regex("""\bloan\s+of\s+rs\.?\s*\d+\s*(?:approved|sanctioned)\b""", RegexOption.IGNORE_CASE),
            Regex("""\bzero\s+(?:interest|cibil|document)\s+loan\b""", RegexOption.IGNORE_CASE)
        ),
        "JOB_SCAM" to listOf(
            Regex("""\bpart\s*time\s+job\s*(?:from\s+home)?\b""", RegexOption.IGNORE_CASE),
            Regex("""\bearn\s+rs\.?\s*\d+\s*(?:daily|per\s+day|hourly)\b""", RegexOption.IGNORE_CASE),
            Regex("""\byoutube\s+(?:like|subscribe|video)\s+and\s+earn\b""", RegexOption.IGNORE_CASE)
        ),
        "INVESTMENT_FRAUD" to listOf(
            Regex("""\bguaranteed\s+(?:returns|profit|income)\b""", RegexOption.IGNORE_CASE),
            Regex("""\bdouble\s+your\s+money\b""", RegexOption.IGNORE_CASE),
            Regex("""\bcrypto\s+(?:trading|investment)\s+returns\b""", RegexOption.IGNORE_CASE)
        )
    )

    private val URL_REGEX = Pattern.compile(
        """(https?://[^\s/$.?#].[^\s]*|(?:www\.)[^\s/$.?#].[^\s]*|[a-zA-Z0-9\-]+(?:\.[a-zA-Z0-9\-]+)*\.(?:com|in|org|net|xyz|top|site|online|club|live|link|vip|app|shop|ru|cn)(?:/[^\s]*)?)""",
        Pattern.CASE_INSENSITIVE
    )

    private val SUSPICIOUS_DOMAINS = listOf(
        "xyz", "top", "site", "online", "club", "live", "link", "vip", "ru", "cn", "cc", "tk"
    )

    fun extractUrls(text: String): List<String> {
        val urls = mutableListOf<String>()
        val matcher = URL_REGEX.matcher(text)
        while (matcher.find()) {
            val url = matcher.group()
            if (url.length >= 4) {
                urls.add(url)
            }
        }
        return urls
    }

    /**
     * Autonomous local AI evaluation of any text content (SMS, Shared Message, Link description).
     * Returns an immediate, non-blocking risk assessment.
     */
    fun evaluate(text: String, sender: String? = null): RiskAssessment {
        val trimmed = text.trim()
        val extractedUrls = extractUrls(trimmed)
        val reasons = mutableListOf<String>()

        var detectedCategory = "BENIGN"
        var maxScore = 0.0f

        // 1. Evaluate known fraud signatures
        for ((category, regexList) in PATTERNS) {
            val textToEvaluate = if (category == "OTP_THEFT") {
                trimmed.replace(
                    Regex("""\b(?:do\s+not|never|don't|dont)\s+share\s+(?:your\s+)?(?:otp|pin|password)\s*(?:with\s+anyone)?\b""", RegexOption.IGNORE_CASE),
                    ""
                )
            } else {
                trimmed
            }

            for (regex in regexList) {
                if (regex.containsMatchIn(textToEvaluate)) {
                    val score = when (category) {
                        "GOV_IMPERSONATION" -> 98.0f
                        "OTP_THEFT"          -> 95.0f
                        "UPI_FRAUD"          -> 92.0f
                        "BANKING_FRAUD"      -> 94.0f
                        "LOTTERY_SCAM"        -> 85.0f
                        "DELIVERY_SCAM"       -> 88.0f
                        "LOAN_SCAM"           -> 80.0f
                        "INVESTMENT_FRAUD"    -> 82.0f
                        "JOB_SCAM"            -> 78.0f
                        else                  -> 70.0f
                    }
                    if (score > maxScore) {
                        maxScore = score
                        detectedCategory = category
                        reasons.add("Detected high-risk signature matching $category: '${regex.find(trimmed)?.value ?: regex.pattern}'")
                    }
                    break
                }
            }
        }

        // 2. High-Pressure Urgency Boost
        val urgencyRegex = Regex(
            """\b(?:urgent|immediately|action\s+required|within\s+\d+\s*(?:minutes?|hours?|mins?|hrs?)|within\s+24\s*hours?)\b""",
            RegexOption.IGNORE_CASE
        )
        val urgencyMatch = urgencyRegex.find(trimmed)
        if (urgencyMatch != null && detectedCategory != "BENIGN") {
            maxScore = (maxScore + 4.0f).coerceAtMost(100.0f)
            reasons.add("High-pressure urgency markers detected ('${urgencyMatch.value}') attempting to induce panic action.")
        }

        // 3. Credential Harvesting Boost
        val credentialRegex = Regex(
            """\b(?:banking\s+credentials|login\s+credentials|passwords?|credentials|netbanking\s+pin)\b""",
            RegexOption.IGNORE_CASE
        )
        val credMatch = credentialRegex.find(trimmed)
        if (credMatch != null && detectedCategory != "BENIGN") {
            maxScore = (maxScore + 4.0f).coerceAtMost(100.0f)
            reasons.add("Credential harvesting attempt targeting sensitive banking authentication credentials.")
        }

        // 4. Evaluate URL threat heuristics if any URLs exist
        if (extractedUrls.isNotEmpty()) {
            for (url in extractedUrls) {
                val lower = url.lowercase()
                val hasSuspiciousTld = SUSPICIOUS_DOMAINS.any { lower.contains(".$it") }
                val hasDeceptiveSubdomain = lower.contains("sbi") || lower.contains("hdfc") ||
                        lower.contains("yono") || lower.contains("kyc") || lower.contains("pan") ||
                        lower.contains("paytm") || lower.contains("phonepe")

                if (hasSuspiciousTld || hasDeceptiveSubdomain) {
                    val boost = if (hasDeceptiveSubdomain) 25.0f else 15.0f
                    maxScore = (maxScore + boost).coerceAtMost(100.0f)
                    if (detectedCategory == "BENIGN") {
                        detectedCategory = "PHISHING_URL"
                    }
                    reasons.add("Suspicious link identified ($url) matching deceptive brand or TLD patterns.")
                }
            }
        }

        // 5. Sender evaluation (suspicious 10-digit mobile numbers sending banking alerts)
        if (sender != null) {
            val cleanSender = sender.replace(Regex("""[^0-9]"""), "")
            if (cleanSender.length == 10 && (detectedCategory == "BANKING_FRAUD" || detectedCategory == "OTP_THEFT")) {
                maxScore = (maxScore + 5.0f).coerceAtMost(100.0f)
                reasons.add("Institutional alert originated from personal 10-digit number ($sender) instead of authorized bank sender ID.")
            }
        }

        // 6. Map final severity and recommendations
        val severity = when {
            maxScore >= 90.0f -> "CRITICAL"
            maxScore >= 70.0f -> "HIGH"
            maxScore >= 40.0f -> "MEDIUM"
            else -> "LOW"
        }

        val recommendedAction = when (severity) {
            "CRITICAL" -> "URGENT: Do not click any links, send money, or share OTPs. This message contains verified fraud signatures."
            "HIGH"     -> "WARNING: Highly suspicious message. Verify directly through official customer support."
            "MEDIUM"   -> "Caution advised: Unverified sender or unconfirmed offer."
            else       -> "Message appears safe. No known threat signatures detected."
        }

        return RiskAssessment(
            category = detectedCategory,
            severity = severity,
            riskScore = maxScore,
            reasons = reasons.ifEmpty { listOf("No threat signatures detected.") },
            recommendedAction = recommendedAction,
            extractedUrls = extractedUrls
        )
    }
}
