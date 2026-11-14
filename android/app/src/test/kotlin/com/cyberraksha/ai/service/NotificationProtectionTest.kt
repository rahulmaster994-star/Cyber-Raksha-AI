package com.cyberraksha.ai.service

import com.cyberraksha.ai.engine.UnifiedRiskEngine
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class NotificationProtectionTest {

    @Test
    fun testWhatsAppBankingSuspensionScamDetection() {
        val preview = "URGENT: Your SBI account has been suspended due to unverified KYC. Immediately update your PAN and banking credentials here: http://bit.ly/sbi-verify to restore access."
        val sender = "+919876543210"
        val result = UnifiedRiskEngine.evaluate(preview, sender)

        assertTrue(result.riskScore >= 80.0f)
        assertEquals("CRITICAL", result.severity)
        assertTrue(result.reasons.isNotEmpty())
    }

    @Test
    fun testTelegramDigitalArrestScamDetection() {
        val preview = "Attention Citizen: CBI and Mumbai Cyber Crime Cell has issued a digital arrest warrant against you. Join Skype video interrogation immediately or police team will reach your home."
        val sender = "Officer Vikram (CBI)"
        val result = UnifiedRiskEngine.evaluate(preview, sender)

        assertTrue(result.riskScore >= 85.0f)
        assertEquals("CRITICAL", result.severity)
    }

    @Test
    fun testWhatsAppPersonalBenignConversation() {
        val preview = "Hey, are we still meeting for lunch at 1 PM today? Let me know when you reach."
        val sender = "Rahul Sharma"
        val result = UnifiedRiskEngine.evaluate(preview, sender)

        assertEquals(0.0f, result.riskScore, 0.01f)
        assertEquals("LOW", result.severity)
    }

    @Test
    fun testWhatsAppLegitimateOtpNotification() {
        val preview = "789123 is your verification code for Swiggy order. Do not share OTP with anyone including delivery partners."
        val sender = "Swiggy"
        val result = UnifiedRiskEngine.evaluate(preview, sender)

        assertEquals(0.0f, result.riskScore, 0.01f)
        assertEquals("LOW", result.severity)
    }
}
