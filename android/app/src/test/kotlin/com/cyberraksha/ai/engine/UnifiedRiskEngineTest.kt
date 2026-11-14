package com.cyberraksha.ai.engine

import org.junit.Assert.*
import org.junit.Test

class UnifiedRiskEngineTest {

    @Test
    fun testUserUrgentKycAccountBlockExactMessage() {
        val message = "URGENT: Your bank account will be blocked within 30 minutes! Your KYC verification has expired. Immediately verify your account and provide your banking credentials to avoid permanent suspension."
        val result = UnifiedRiskEngine.evaluate(message, "+919876543210")

        assertEquals("BANKING_FRAUD", result.category)
        assertEquals("CRITICAL", result.severity)
        assertTrue("Risk score should be >= 95", result.riskScore >= 95f)
        assertTrue(result.reasons.any { it.contains("BANKING_FRAUD") })
        assertTrue(result.reasons.any { it.contains("urgency") })
        assertTrue(result.reasons.any { it.contains("Credential") })
    }

    @Test
    fun testDigitalArrestFraudDetection() {
        val message = "This is DCP Cyber Cell Delhi. An arrest warrant has been issued in your name for money laundering. Contact immediately on Skype or attend digital arrest hearing."
        val result = UnifiedRiskEngine.evaluate(message, "POLICE-NOTICE")

        assertEquals("GOV_IMPERSONATION", result.category)
        assertTrue("Risk score should be high/critical", result.riskScore >= 75f)
        assertTrue(result.severity == "HIGH" || result.severity == "CRITICAL")
        assertTrue(result.reasons.isNotEmpty())
    }

    @Test
    fun testOtpTheftDetection() {
        val message = "Your SBI OTP for transaction of Rs 45,000 is 849201. Do not share OTP with anyone. Bank employee asking for OTP to verify debit card."
        val result = UnifiedRiskEngine.evaluate(message, "SBI-ALERT")

        assertEquals("OTP_THEFT", result.category)
        assertTrue(result.riskScore >= 70f)
        assertTrue(result.severity == "HIGH" || result.severity == "CRITICAL")
    }

    @Test
    fun testUpiPaymentScamDetection() {
        val message = "Dear user, you received a PhonePe collect request of Rs 25,000. Enter your UPI PIN to receive money in your account."
        val result = UnifiedRiskEngine.evaluate(message, "PHONEPE-ALERT")

        assertEquals("UPI_FRAUD", result.category)
        assertTrue(result.riskScore >= 70f)
    }

    @Test
    fun testBankingKycSuspensionScamDetection() {
        val message = "Dear Customer, Your HDFC Bank account is suspended today due to pending KYC verification. Click here to update pan card: http://hdfc-kyc-verify.xyz"
        val result = UnifiedRiskEngine.evaluate(message, "HDFC-BANK")

        assertEquals("BANKING_FRAUD", result.category)
        assertTrue(result.riskScore >= 75f)
        assertEquals("CRITICAL", result.severity)
        assertTrue(result.extractedUrls.contains("http://hdfc-kyc-verify.xyz"))
    }

    @Test
    fun testDeliveryPackageScamDetection() {
        val message = "India Post: Your parcel has arrived at warehouse but cannot be delivered due to incomplete address. Update address within 24h: https://indiapost-parcel.top"
        val result = UnifiedRiskEngine.evaluate(message, "INDPOST")

        assertEquals("DELIVERY_SCAM", result.category)
        assertTrue(result.riskScore >= 65f)
        assertTrue(result.severity == "HIGH" || result.severity == "CRITICAL")
    }

    @Test
    fun testLegitimateBankingSalaryCreditAlert() {
        val message = "Dear Customer, your salary of Rs 75,000 has been credited to your A/c XX1234 on 01-Nov-24. Avl Bal: Rs 1,12,000. - HDFC Bank"
        val result = UnifiedRiskEngine.evaluate(message, "HDFC-BNK")

        assertEquals("BENIGN", result.category)
        assertEquals("LOW", result.severity)
        assertEquals(0f, result.riskScore, 0.01f)
    }

    @Test
    fun testLegitimateMerchantOtpAlert() {
        val message = "123456 is your OTP for purchase of Rs 499 at Swiggy. Do not share OTP with anyone for security reasons."
        val result = UnifiedRiskEngine.evaluate(message, "SWIGGY")

        assertEquals("BENIGN", result.category)
        assertEquals("LOW", result.severity)
        assertEquals(0f, result.riskScore, 0.01f)
    }

    @Test
    fun testBenignPersonalMessage() {
        val message = "Hi Rahul, are we still meeting for lunch tomorrow at 1 PM?"
        val result = UnifiedRiskEngine.evaluate(message, "+919876543210")

        assertEquals("BENIGN", result.category)
        assertEquals(0f, result.riskScore, 0.01f)
        assertEquals("LOW", result.severity)
        assertEquals(listOf("No threat signatures detected."), result.reasons)
    }
}
