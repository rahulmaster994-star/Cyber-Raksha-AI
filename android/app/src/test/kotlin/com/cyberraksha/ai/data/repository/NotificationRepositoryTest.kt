package com.cyberraksha.ai.data.repository

import com.cyberraksha.ai.data.local.NotificationDao
import com.cyberraksha.ai.data.local.NotificationEntity
import com.cyberraksha.ai.data.remote.CyberRakshaApiService
import com.cyberraksha.ai.data.remote.NotificationItem
import com.cyberraksha.ai.data.remote.NotificationListResponse
import io.mockk.coEvery
import io.mockk.coVerify
import io.mockk.mockk
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.flowOf
import kotlinx.coroutines.runBlocking
import okhttp3.ResponseBody.Companion.toResponseBody
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test
import retrofit2.Response

class NotificationRepositoryTest {

    private lateinit var api: CyberRakshaApiService
    private lateinit var dao: NotificationDao
    private lateinit var repository: NotificationRepository

    @Before
    fun setup() {
        api = mockk()
        dao = mockk(relaxed = true)
        repository = NotificationRepository(api, dao)
    }

    @Test
    fun `getNotificationsFlow reads directly from dao`() = runBlocking {
        val fakeEntities = listOf(
            NotificationEntity(
                id = 1,
                title = "Phishing Detected",
                message = "Blocked attempt",
                severity = "CRITICAL",
                category = "PHISHING",
                targetDomain = "evil.example.invalid",
                isRead = false,
                createdAt = "2026-11-09T10:00:00Z",
                sourceComponent = "EXTENSION_DNR"
            )
        )
        coEvery { dao.getAll(100) } returns flowOf(fakeEntities)

        val result = repository.getNotificationsFlow(100).first()

        assertEquals(1, result.size)
        assertEquals("Phishing Detected", result[0].title)
    }

    @Test
    fun `syncFromBackend success upserts to dao and returns true`() = runBlocking {
        val fakeApiList = listOf(
            NotificationItem(
                id = 42,
                title = "Malicious URL Blocked",
                message = "Protected user",
                severity = "HIGH",
                category = "MALWARE",
                targetDomain = "bad.example.invalid",
                isRead = false,
                createdAt = "2026-11-09T10:10:00Z",
                sourceComponent = "EXTENSION_DNR"
            )
        )
        coEvery { api.getNotifications(limit = 100) } returns Response.success(
            NotificationListResponse(
                notifications = fakeApiList,
                total = 1,
                unreadCount = 1
            )
        )

        val success = repository.syncFromBackend()

        assertTrue(success)
        coVerify(exactly = 1) { dao.upsertAll(any()) }
    }

    @Test
    fun `syncFromBackend failure returns false and does not throw`() = runBlocking {
        coEvery { api.getNotifications(limit = 100) } returns Response.error(
            500,
            "Internal Server Error".toResponseBody()
        )

        val success = repository.syncFromBackend()

        assertFalse(success)
        coVerify(exactly = 0) { dao.upsertAll(any()) }
    }
}

