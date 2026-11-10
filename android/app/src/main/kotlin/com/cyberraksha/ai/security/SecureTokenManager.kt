package com.cyberraksha.ai.security

import android.os.Build
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.Base64
import java.nio.ByteBuffer
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec
import javax.crypto.spec.SecretKeySpec

/**
 * Cyber Raksha AI - Hardware-Backed Secure Token Storage
 * Phase B2.1 & B3: Unified Protection Integration
 *
 * Encrypts and decrypts device authentication tokens at rest using AES-256-GCM
 * with keys stored in the Android hardware KeyStore.
 * Provides fallback for unit test JVM environments where AndroidKeyStore is absent.
 */
object SecureTokenManager {

    private const val ANDROID_KEYSTORE = "AndroidKeyStore"
    private const val KEY_ALIAS = "cyber_raksha_device_auth_key"
    private const val TRANSFORMATION = "AES/GCM/NoPadding"
    private const val GCM_TAG_LENGTH = 128
    private const val IV_LENGTH = 12

    // Fallback key STRICTLY for standard non-Android JVM unit tests
    private val JVM_FALLBACK_KEY = SecretKeySpec(
        "CYBER_RAKSHA_JVM_FALLBACK_KEY_32B".toByteArray().copyOf(32),
        "AES"
    )

    /**
     * Detects if the current process is running inside an actual Android OS environment.
     * Host JVM unit tests will have SDK_INT == 0 or throw ClassNotFound.
     */
    fun isAndroidRuntime(): Boolean {
        return try {
            Build.VERSION.SDK_INT > 0
        } catch (e: Throwable) {
            false
        }
    }

    private fun getOrCreateKey(): SecretKey {
        if (!isAndroidRuntime()) {
            // Unit test environment only
            return JVM_FALLBACK_KEY
        }

        // Production Android OS: strictly use AndroidKeyStore
        val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
        return if (!keyStore.containsAlias(KEY_ALIAS)) {
            val keyGenerator = KeyGenerator.getInstance(
                KeyProperties.KEY_ALGORITHM_AES,
                ANDROID_KEYSTORE
            )
            val keyGenParameterSpec = KeyGenParameterSpec.Builder(
                KEY_ALIAS,
                KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
            )
                .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
                .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
                .setKeySize(256)
                .build()

            keyGenerator.init(keyGenParameterSpec)
            keyGenerator.generateKey()
        } else {
            val entry = keyStore.getEntry(KEY_ALIAS, null) as KeyStore.SecretKeyEntry
            entry.secretKey
        }
    }

    /**
     * Encrypts plaintext token using AES-GCM and prepends the unique IV.
     * Output is Base64 encoded. Never returns plaintext on error.
     */
    fun encrypt(plainText: String): String {
        if (plainText.isBlank()) return ""
        return try {
            val key = getOrCreateKey()
            val cipher = Cipher.getInstance(TRANSFORMATION)
            cipher.init(Cipher.ENCRYPT_MODE, key)
            val iv = cipher.iv
            val cipherText = cipher.doFinal(plainText.toByteArray(Charsets.UTF_8))

            val byteBuffer = ByteBuffer.allocate(iv.size + cipherText.size)
            byteBuffer.put(iv)
            byteBuffer.put(cipherText)

            encodeBase64(byteBuffer.array())
        } catch (e: Exception) {
            // Defense-in-depth: Never persist plaintext tokens to disk if encryption fails
            ""
        }
    }

    /**
     * Decrypts Base64 payload, extracts IV, and decrypts ciphertext using AES-GCM.
     * Returns empty string on decryption failure (forcing re-auth), never corrupted data.
     */
    fun decrypt(encryptedBase64: String): String {
        if (encryptedBase64.isBlank()) return ""
        return try {
            val combined = decodeBase64(encryptedBase64)
            if (combined.size <= IV_LENGTH) return ""

            val iv = combined.copyOfRange(0, IV_LENGTH)
            val cipherText = combined.copyOfRange(IV_LENGTH, combined.size)

            val key = getOrCreateKey()
            val cipher = Cipher.getInstance(TRANSFORMATION)
            val spec = GCMParameterSpec(GCM_TAG_LENGTH, iv)
            cipher.init(Cipher.DECRYPT_MODE, key, spec)

            String(cipher.doFinal(cipherText), Charsets.UTF_8)
        } catch (e: Exception) {
            // Decryption failure (key invalidated, corrupt data, or tampered payload)
            ""
        }
    }

    /**
     * Wipes KeyStore alias and invalidated cryptographic keys on logout or device revocation.
     */
    fun wipeCredentials() {
        try {
            if (isAndroidRuntime()) {
                val keyStore = KeyStore.getInstance(ANDROID_KEYSTORE).apply { load(null) }
                if (keyStore.containsAlias(KEY_ALIAS)) {
                    keyStore.deleteEntry(KEY_ALIAS)
                }
            }
        } catch (e: Exception) {
            // Ignore wipe failures during process teardown
        }
    }

    private fun encodeBase64(bytes: ByteArray): String {
        return try {
            Base64.encodeToString(bytes, Base64.NO_WRAP)
        } catch (e: Exception) {
            java.util.Base64.getEncoder().encodeToString(bytes)
        }
    }

    private fun decodeBase64(str: String): ByteArray {
        return try {
            Base64.decode(str, Base64.NO_WRAP)
        } catch (e: Exception) {
            java.util.Base64.getDecoder().decode(str)
        }
    }
}

