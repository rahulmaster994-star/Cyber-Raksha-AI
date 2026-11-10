package com.cyberraksha.ai.notifications

import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.ActivityCompat
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import com.cyberraksha.ai.MainActivity
import android.R as AndroidR

object NotificationHelper {

    const val CHANNEL_CRITICAL = "cyber_raksha_critical"
    const val CHANNEL_HIGH     = "cyber_raksha_high"
    const val CHANNEL_GENERAL  = "cyber_raksha_general"

    fun createChannels(context: Context) {
        val manager = context.getSystemService(Context.NOTIFICATION_SERVICE)
                as NotificationManager

        manager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_CRITICAL,
                "Critical Threats",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "Critical security threats requiring immediate attention"
                enableVibration(true)
            }
        )

        manager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_HIGH,
                "High Priority Alerts",
                NotificationManager.IMPORTANCE_DEFAULT
            ).apply {
                description = "High priority security alerts"
            }
        )

        manager.createNotificationChannel(
            NotificationChannel(
                CHANNEL_GENERAL,
                "Security Notifications",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "General security notifications and updates"
            }
        )
    }

    fun showNotification(
        context: Context,
        title: String,
        message: String,
        severity: String,
        notificationId: Int
    ) {
        // Android 13+: check POST_NOTIFICATIONS permission
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            if (ActivityCompat.checkSelfPermission(
                    context,
                    android.Manifest.permission.POST_NOTIFICATIONS
                ) != PackageManager.PERMISSION_GRANTED
            ) return
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
            .setContentIntent(pendingIntent)
            .setAutoCancel(true)
            .build()

        NotificationManagerCompat.from(context).notify(notificationId, notification)
    }
}

