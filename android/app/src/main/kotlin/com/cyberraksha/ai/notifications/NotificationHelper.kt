package com.cyberraksha.ai.notifications

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.util.Log
import androidx.core.app.ActivityCompat
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.cyberraksha.ai.MainActivity
import android.R as AndroidR

object NotificationHelper {

    private const val TAG = "NotificationHelper"
    const val CHANNEL_CRITICAL = "cyber_raksha_critical"
    const val CHANNEL_HIGH     = "cyber_raksha_high"
    const val CHANNEL_GENERAL  = "cyber_raksha_general"

    fun createChannels(context: Context) {
        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE) as? NotificationManager ?: return

        val criticalChannel = NotificationChannel(
            CHANNEL_CRITICAL,
            "Critical Security Threats",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = "High-priority critical alerts for financial fraud, OTP theft, and digital arrest threats"
            enableVibration(true)
            setShowBadge(true)
        }

        val highChannel = NotificationChannel(
            CHANNEL_HIGH,
            "High Priority Alerts",
            NotificationManager.IMPORTANCE_HIGH
        ).apply {
            description = "Important security warnings and suspicious activity alerts"
            enableVibration(true)
            setShowBadge(true)
        }

        val generalChannel = NotificationChannel(
            CHANNEL_GENERAL,
            "Security Status & Diagnostics",
            NotificationManager.IMPORTANCE_DEFAULT
        ).apply {
            description = "General security updates and status sync notifications"
        }

        manager.createNotificationChannels(listOf(criticalChannel, highChannel, generalChannel))
    }

    fun showNotification(
        context: Context,
        title: String,
        message: String,
        severity: String,
        notificationId: Int
    ): Boolean {
        // Ensure channels are created even if invoked before MainActivity launches
        createChannels(context)

        // Android 13+: check POST_NOTIFICATIONS permission
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            val hasPermission = ActivityCompat.checkSelfPermission(
                context,
                android.Manifest.permission.POST_NOTIFICATIONS
            ) == PackageManager.PERMISSION_GRANTED

            if (!hasPermission) {
                Log.w(TAG, "POST_NOTIFICATIONS permission NOT granted. Notification cannot be displayed.")
                return false
            }
        }

        val channel = when (severity.uppercase()) {
            "CRITICAL" -> CHANNEL_CRITICAL
            "HIGH"     -> CHANNEL_HIGH
            else       -> CHANNEL_GENERAL
        }

        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        val pendingIntent = PendingIntent.getActivity(
            context, 0, intent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )

        val notification = NotificationCompat.Builder(context, channel)
            .setSmallIcon(AndroidR.drawable.ic_dialog_alert)
            .setContentTitle(title)
            .setContentText(message)
            .setStyle(NotificationCompat.BigTextStyle().bigText(message))
            .setPriority(
                when (severity.uppercase()) {
                    "CRITICAL" -> NotificationCompat.PRIORITY_MAX
                    "HIGH"     -> NotificationCompat.PRIORITY_HIGH
                    else       -> NotificationCompat.PRIORITY_DEFAULT
                }
            )
            .setDefaults(NotificationCompat.DEFAULT_ALL)
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()

        return try {
            NotificationManagerCompat.from(context).notify(notificationId, notification)
            Log.i(TAG, "Notification successfully posted: id=$notificationId, title='$title'")
            true
        } catch (e: Exception) {
            Log.e(TAG, "Failed to post notification id=$notificationId", e)
            false
        }
    }
}
