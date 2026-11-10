package com.cyberraksha.ai.security

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertTrue
import org.junit.Test

/**
 * Unit tests for SecureTokenManager verifying AES-256-GCM encryption,
 * decryption failure safety (never leaks plaintext), IV integrity,
 * and credential wiping.
 */
class SecureTokenManagerTest {

    @Test
    fun testIsAndroidRuntime_returnsFalseInHostJvm() {
        // In local JVM Gradle unit tests, Android Build.VERSION.SDK_INT is 0
        assertFalse(SecureTokenManager.isAndroidRuntime())
    }

    @Test
    fun testEncryptDecrypt_roundtripSuccess() {
        val originalToken = "CR_DEVICE_TOKEN_SECURE_UUID_999888"
        val encrypted = SecureTokenManager.encrypt(originalToken)

        assertTrue(encrypted.isNotBlank())
        assertNotEquals(originalToken, encrypted)

        val decrypted = SecureTokenManager.decrypt(encrypted)
        assertEquals(originalToken, decrypted)
    }

    @Test
    fun testEncrypt_emptyOrBlankReturnsEmpty() {
        assertEquals("", SecureTokenManager.encrypt(""))
        assertEquals("", SecureTokenManager.encrypt("   "))
    }

    @Test
    fun testDecrypt_emptyOrBlankReturnsEmpty() {
        assertEquals("", SecureTokenManager.decrypt(""))
        assertEquals("", SecureTokenManager.decrypt("   "))
    }

    @Test
    fun testDecrypt_corruptedOrInvalidCiphertext_returnsEmpty() {
        val corrupted = "NOT_A_VALID_BASE64_CIPHERTEXT!!!"
        val result = SecureTokenManager.decrypt(corrupted)
        assertEquals("", result)
    }

    @Test
    fun testDecrypt_truncatedPayloadBelowIvLength_returnsEmpty() {
        // A base64 payload that decodes to less than 12 bytes
        val shortBase64 = "AQIDBAU=" // 5 bytes
        val result = SecureTokenManager.decrypt(shortBase64)
        assertEquals("", result)
    }

    @Test
    fun testDecrypt_tamperedCiphertext_returnsEmpty() {
        val originalToken = "AUTHENTICATED_DEVICE_TOKEN_SECRET"
        val encrypted = SecureTokenManager.encrypt(originalToken)
        val decoded = java.util.Base64.getDecoder().decode(encrypted)

        // Tamper with the last byte of the auth tag
        decoded[decoded.size - 1] = (decoded[decoded.size - 1].toInt() xor 0xFF).toByte()
        val tamperedBase64 = java.util.Base64.getEncoder().encodeToString(decoded)

        // Decryption must fail and return ""
        val result = SecureTokenManager.decrypt(tamperedBase64)
        assertEquals("", result)
    }

    @Test
    fun testWipeCredentials_executesWithoutException() {
        SecureTokenManager.wipeCredentials()
        // Ensure subsequent operations remain functional
        val token = "TEST_TOKEN_AFTER_WIPE"
        val encrypted = SecureTokenManager.encrypt(token)
        assertEquals(token, SecureTokenManager.decrypt(encrypted))
    }
}

