package com.cyberraksha.ai

import android.Manifest
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.core.content.ContextCompat
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import androidx.lifecycle.lifecycleScope
import android.content.Intent
import android.widget.Toast
import androidx.room.Room
import com.cyberraksha.ai.data.local.AppDatabase
import com.cyberraksha.ai.data.local.ThreatIncidentEntity
import com.cyberraksha.ai.data.remote.SecurityEventApiRequest
import com.cyberraksha.ai.engine.UnifiedRiskEngine
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.remote.NetworkModule
import com.cyberraksha.ai.notifications.NotificationHelper
import com.cyberraksha.ai.sync.SyncScheduler
import com.cyberraksha.ai.ui.CyberRakshaNavHost
import com.cyberraksha.ai.ui.theme.CyberRakshaTheme
import kotlinx.coroutines.flow.firstOrNull
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {

    private val requestCorePermissionsLauncher =
        registerForActivityResult(ActivityResultContracts.RequestMultiplePermissions()) { results ->
            val smsGranted = results[Manifest.permission.RECEIVE_SMS] == true
            val notifGranted = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
                results[Manifest.permission.POST_NOTIFICATIONS] == true
            } else true
            android.util.Log.i("MainActivity", "Core permissions updated -> RECEIVE_SMS=$smsGranted, POST_NOTIFICATIONS=$notifGranted")

            if (smsGranted) {
                lifecycleScope.launch {
                    val prefs = AppPreferences(applicationContext)
                    prefs.setAutonomousProtectionEnabled(true)
                    prefs.setSmsProtectionEnabled(true)
                }
            }
        }

    override fun onCreate(savedInstanceState: Bundle?) {
        installSplashScreen()
        super.onCreate(savedInstanceState)

        val prefs = AppPreferences(applicationContext)

        // Restore authenticated device token into NetworkModule
        lifecycleScope.launch {
            val token = prefs.deviceToken.firstOrNull()
            if (!token.isNullOrBlank()) {
                NetworkModule.setDeviceToken(token)
            }
        }

        // Initialize Android notification channels
        NotificationHelper.createChannels(applicationContext)

        // Request Core Security Permissions (SMS Interception + Notifications)
        checkAndRequestCorePermissions()

        // Schedule periodic background WorkManager sync
        SyncScheduler.schedule(applicationContext)

        // Handle Cross-Application Share Intent (WhatsApp, Telegram, Browser URLs)
        handleIncomingShareIntent(intent)

        setContent {
            CyberRakshaTheme {
                CyberRakshaNavHost(prefs = prefs)
            }
        }
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        handleIncomingShareIntent(intent)
    }

    private fun checkAndRequestCorePermissions() {
        val permissionsToRequest = mutableListOf<String>()

        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECEIVE_SMS) != PackageManager.PERMISSION_GRANTED) {
            permissionsToRequest.add(Manifest.permission.RECEIVE_SMS)
        }
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.READ_SMS) != PackageManager.PERMISSION_GRANTED) {
            permissionsToRequest.add(Manifest.permission.READ_SMS)
        }
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED) {
                permissionsToRequest.add(Manifest.permission.POST_NOTIFICATIONS)
            }
        }

        if (permissionsToRequest.isNotEmpty()) {
            requestCorePermissionsLauncher.launch(permissionsToRequest.toTypedArray())
        }
    }

    private fun handleIncomingShareIntent(intent: Intent?) {
        if (intent?.action != Intent.ACTION_SEND || intent.type != "text/plain") return
        val sharedText = intent.getStringExtra(Intent.EXTRA_TEXT)?.trim() ?: return
        if (sharedText.isBlank()) return

        lifecycleScope.launch(kotlinx.coroutines.Dispatchers.IO) {
            val assessment = UnifiedRiskEngine.evaluate(sharedText)
            val db = Room.databaseBuilder(
                applicationContext,
                AppDatabase::class.java,
                "cyber_raksha_db"
            ).fallbackToDestructiveMigration().build()

            val incId = db.threatIncidentDao().insertIncident(
                ThreatIncidentEntity(
                    incidentType = "SHARED_SCAN",
                    indicator = assessment.extractedUrls.firstOrNull() ?: sharedText.take(40),
                    category = assessment.category,
                    severity = assessment.severity,
                    riskScore = assessment.riskScore,
                    description = "Cross-app scan: ${assessment.reasons.firstOrNull() ?: assessment.category}"
                )
            )

            if (assessment.severity == "CRITICAL" || assessment.severity == "HIGH") {
                NotificationHelper.showNotification(
                    context = applicationContext,
                    title = "🚨 Malicious Content Detected (${assessment.category})",
                    message = assessment.recommendedAction,
                    severity = assessment.severity,
                    notificationId = sharedText.hashCode()
                )
            }

            try {
                val prefs = com.cyberraksha.ai.core.AppPreferences(applicationContext)
                val deviceId = prefs.deviceId.firstOrNull() ?: "android-device"
                val api = NetworkModule.getApiService()
                api.reportSecurityEvent(
                    SecurityEventApiRequest(
                        eventType = "SHARED_CONTENT_SCANNED",
                        severity = assessment.severity,
                        sourceComponent = "ANDROID_SHARE_TARGET",
                        deviceId = deviceId,
                        threatIndicator = assessment.extractedUrls.firstOrNull() ?: sharedText.take(50),
                        riskScore = assessment.riskScore,
                        detectionReason = assessment.category,
                        description = "Scanned shared content: ${assessment.category}"
                    )
                )
                db.threatIncidentDao().markAsSynced(listOf(incId))
            } catch (_: Exception) {}

            db.close()
        }
    }
}

