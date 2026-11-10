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
import com.cyberraksha.ai.core.AppPreferences
import com.cyberraksha.ai.data.remote.NetworkModule
import com.cyberraksha.ai.notifications.NotificationHelper
import com.cyberraksha.ai.sync.SyncScheduler
import com.cyberraksha.ai.ui.CyberRakshaNavHost
import com.cyberraksha.ai.ui.theme.CyberRakshaTheme
import kotlinx.coroutines.flow.firstOrNull
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {

    private val requestNotificationPermissionLauncher =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { isGranted ->
            // Permission result handled; notifications will be posted if granted
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

        // Request POST_NOTIFICATIONS permission on Android 13+ (API 33+)
        checkAndRequestNotificationPermission()

        // Schedule periodic background WorkManager sync
        SyncScheduler.schedule(applicationContext)

        setContent {
            CyberRakshaTheme {
                CyberRakshaNavHost(prefs = prefs)
            }
        }
    }

    private fun checkAndRequestNotificationPermission() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            val permissionStatus = ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.POST_NOTIFICATIONS
            )
            if (permissionStatus != PackageManager.PERMISSION_GRANTED) {
                requestNotificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
    }
}

